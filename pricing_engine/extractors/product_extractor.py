import json
import re
from urllib.parse import parse_qs, urlparse


class ProductExtractor:
    """
    SHEIN Product Extractor - one-shot robust version.

    Sources, in priority order:
      1. Rendered product-card DOM (name, visible price, data-expose-id)
      2. Embedded page state in the current HTML (exact goods_id/name/price)
      3. Already-captured network JSON (enrichment only)

    This class NEVER clicks cards and NEVER navigates to product pages.
    """

    CARD_SELECTORS = [
        "[class*='product-card']",
        "[class*='productCard']",
        "[class*='goods-card']",
        "[class*='goodsCard']",
    ]

    def __init__(self, page):
        self.page = page

    async def extract(self):
        print("=" * 70)
        print("PRODUCT EXTRACTOR")
        print("=" * 70)

        cards = await self.find_product_cards()
        if cards is None:
            print("[PRODUCT] No product cards found.")
            return []

        card_count = await cards.count()
        print(f"[PRODUCT] Product cards found: {card_count}")
        if card_count == 0:
            return []

        dom_products = await self.extract_cards_from_dom(cards)
        print(f"[PRODUCT] RAW PRODUCTS: {len(dom_products)}")

        normalized = self._normalize_many(dom_products)
        print(f"[PRODUCT] NORMALIZED PRODUCTS: {len(normalized)}")

        # Exact data embedded in the CURRENT page. This is the key fix for
        # cards whose visible DOM does not contain a price.
        try:
            embedded_products = await self.extract_from_page_state()
            print(f"[PRODUCT] Embedded page products found: {len(embedded_products)}")
            normalized = self.merge_products(normalized, embedded_products, source="embedded")
        except Exception as exc:
            print(f"[PRODUCT] Embedded page extraction failed: {exc!r}")

        # Network is last and enrichment-only. It must never create random
        # products merely because an ID appeared in an unrelated response.
        try:
            network_products = await self.extract_from_network()
            print(f"[PRODUCT] Network products found: {len(network_products)}")
            normalized = self.merge_products(normalized, network_products, source="network")
        except Exception as exc:
            print(f"[PRODUCT] Network extraction failed: {exc!r}")

        # Final identity/URL cleanup.
        final = []
        for product in normalized:
            product = self._finalize_product(product)
            if product is not None:
                final.append(product)

        final = self.dedupe_products(final)

        # The scraper's downstream ClickHouse pipeline expects a real price.
        # Do not emit ID/name-only records as if their price were known.
        priced_final = []
        for product in final:
            if self.has_valid_money(product.get("price", "")):
                priced_final.append(product)

        skipped_no_price = len(final) - len(priced_final)
        if skipped_no_price:
            print(f"[PRODUCT] Skipped {skipped_no_price} products with no valid price")

        final = priced_final

        print("=" * 70)
        print(f"[PRODUCT] PRODUCTS FOUND: {len(final)}")
        print("=" * 70)

        for i, product in enumerate(final, 1):
            print(
                f"[PRODUCT {i}] {product.get('name', '')} | "
                f"{product.get('price', '')} | "
                f"{product.get('product_id', '')}"
            )
            print(f"    URL: {product.get('product_url', '')}")

        return final

    def _normalize_many(self, products):
        result = []
        for index, product in enumerate(products or []):
            try:
                item = self.normalize_product(product)
                if item:
                    result.append(item)
            except Exception as exc:
                print(f"[PRODUCT] Normalization error at index {index}: {exc!r}")
        return result

    async def find_product_cards(self):
        best = None
        best_count = 0
        for selector in self.CARD_SELECTORS:
            try:
                locator = self.page.locator(selector)
                count = await locator.count()
                print(f"[PRODUCT] Selector: {selector} -> {count}")
                if count > best_count:
                    best = locator
                    best_count = count
            except Exception as exc:
                print(f"[PRODUCT] Selector error {selector}: {exc!r}")
        if best is not None:
            print(f"[PRODUCT] Selected count: {best_count}")
        return best

    async def extract_cards_from_dom(self, cards):
        javascript = r"""
        (cards) => {
            function clean(v) {
                if (v === null || v === undefined) return "";
                return String(v).replace(/\s+/g, " ").trim();
            }

            function attr(el, name) {
                try { return clean(el.getAttribute(name)); } catch (e) { return ""; }
            }

            function allElements(root) {
                const out = [root];
                try { root.querySelectorAll("*").forEach(x => out.push(x)); } catch (e) {}
                return out;
            }

            function findUrl(card) {
                for (const el of allElements(card)) {
                    const values = [];
                    if (el.tagName === "A") values.push(attr(el, "href"));
                    for (const key of [
                        "href", "data-href", "data-url", "data-product-url",
                        "data-producturl", "data-link", "data-detail-url",
                        "data-detailurl", "data-goods-url", "data-goodsurl"
                    ]) values.push(attr(el, key));

                    for (const value of values) {
                        if (!value) continue;
                        if (/-p-\d{4,}/i.test(value) || /\/product(?:-detail)?\//i.test(value)) {
                            return value;
                        }
                    }
                }
                return "";
            }

            function findId(card, url) {
                // Exact SHEIN card identity. Example: 0-499661993 -> 499661993.
                const expose = attr(card, "data-expose-id");
                const exposeMatch = expose.match(/(\d+)$/);
                if (exposeMatch) return exposeMatch[1];

                const values = [];
                if (url) values.push(url);
                for (const el of allElements(card)) {
                    for (const a of Array.from(el.attributes || [])) values.push(a.value);
                    try { if (el.href) values.push(el.href); } catch (e) {}
                    try {
                        if (el.tagName === "IMG") {
                            if (el.src) values.push(el.src);
                            if (el.currentSrc) values.push(el.currentSrc);
                        }
                    } catch (e) {}
                }

                for (const raw of values) {
                    const text = clean(raw);
                    if (!text) continue;
                    let m = text.match(/-p-(\d{4,})/i);
                    if (m) return m[1];
                    m = text.match(/(?:goods[_-]?id|goodsId|product[_-]?id|productId)["'=:\s]+(\d{4,})/i);
                    if (m) return m[1];
                    try {
                        const u = new URL(text, location.origin);
                        for (const key of ["goods_id", "goodsId", "product_id", "productId", "id"]) {
                            const v = u.searchParams.get(key);
                            if (v && /^\d{4,}$/.test(v)) return v;
                        }
                    } catch (e) {}
                }
                return "";
            }

            function findName(card) {
                for (const img of card.querySelectorAll("img")) {
                    const alt = attr(img, "alt");
                    if (alt && alt.length >= 3 && !/^image$/i.test(alt)) return alt;
                }
                for (const el of card.querySelectorAll("[title]")) {
                    const v = attr(el, "title");
                    if (v && v.length >= 3 && v.length <= 500) return v;
                }
                const ownAria = attr(card, "aria-label");
                if (ownAria && ownAria.length >= 3 && ownAria.length <= 500) return ownAria;
                for (const el of card.querySelectorAll("[aria-label]")) {
                    const v = attr(el, "aria-label");
                    if (v && v.length >= 3 && v.length <= 500) return v;
                }
                for (const selector of ["[class*='name']", "[class*='Name']", "[class*='title']", "[class*='Title']"]) {
                    for (const el of card.querySelectorAll(selector)) {
                        const v = clean(el.innerText);
                        if (v && v.length >= 3 && v.length <= 500 && !/^\$?\d+(?:[.,]\d+)?$/.test(v)) return v;
                    }
                }
                for (const el of card.querySelectorAll("a")) {
                    const v = clean(el.innerText);
                    if (v && v.length >= 3 && v.length <= 500) return v;
                }
                return "";
            }

            function findPrice(card) {
                const money = /(?:[$€£]\s*\d+(?:[.,]\d{1,2})?|\b(?:USD|EUR|GBP)\s*\d+(?:[.,]\d{1,2})?)/i;
                for (const el of card.querySelectorAll("[aria-label]")) {
                    const v = attr(el, "aria-label");
                    const m = v.match(money);
                    if (m) return m[0];
                }
                for (const selector of [
                    ".bff-price-container", "[class*='price']", "[class*='Price']",
                    "[class*='sale-price']", "[class*='salePrice']",
                    "[class*='current-price']", "[class*='currentPrice']",
                    "[class*='product-price']", "[class*='productPrice']"
                ]) {
                    for (const el of card.querySelectorAll(selector)) {
                        const v = clean(el.innerText);
                        const m = v.match(money);
                        if (m) return m[0];
                    }
                }
                const m = clean(card.innerText).match(money);
                return m ? m[0] : "";
            }

            return cards.map(card => {
                try {
                    const url = findUrl(card);
                    return {
                        name: findName(card),
                        price: findPrice(card),
                        product_id: findId(card, url),
                        product_url: url,
                    };
                } catch (e) {
                    return {name: "", price: "", product_id: "", product_url: ""};
                }
            });
        }
        """
        try:
            result = await cards.evaluate_all(javascript)
            return result if isinstance(result, list) else []
        except Exception as exc:
            print(f"[PRODUCT] DOM extraction error: {exc!r}")
            return []

    # ------------------------------------------------------------
    # EMBEDDED PAGE STATE
    # ------------------------------------------------------------

    async def extract_from_page_state(self):
        """Read product data already present in the current page HTML.

        SHEIN's rendered page contains productsV2 data with exact goods_id,
        goods_name and salePrice.amount. We parse that current page snapshot;
        no request, click, or navigation is performed.
        """
        html = await self.page.content()
        if not html:
            return []

        products = []
        seen = set()

        # Primary pattern: goods_id -> goods_name -> salePrice/current price.
        # Keep the window deliberately bounded so an unrelated product cannot
        # be associated with an ID.
        id_pattern = re.compile(r'"goods_id"\s*:\s*"?(\d{4,})"?', re.I)
        name_pattern = re.compile(r'"(?:goods_name|goodsName)"\s*:\s*"((?:\\.|[^"\\])*)"', re.I)
        price_pattern = re.compile(
            r'"(?:salePrice|sale_price|currentPrice|current_price|price)"\s*:\s*'
            r'(?:\{\s*)?"?(?:amount|value)?"?\s*:\s*"?([0-9]+(?:[.,][0-9]{1,2})?)"?',
            re.I,
        )

        for match in id_pattern.finditer(html):
            product_id = match.group(1)
            if product_id in seen:
                continue

            start = match.start()
            window = html[start:start + 5000]
            name_match = name_pattern.search(window)
            if not name_match:
                continue

            name = self._decode_json_string(name_match.group(1))
            if not name or self.is_invalid_product_name(name) or self.is_price_like(name):
                continue

            # Prefer salePrice; if not present, use another supported price field.
            price_match = price_pattern.search(window)
            price = price_match.group(1) if price_match else ""

            # The broad price regex can cross into a neighboring object in a
            # pathological response. Validate it as a normal money value.
            if price and not self.is_numeric_price(price):
                price = ""

            products.append({
                "name": name,
                "price": f"${price}" if price else "",
                "product_id": product_id,
                "product_url": "",
            })
            seen.add(product_id)

        # Secondary pattern: some page state uses numeric goods_id values.
        if not products:
            numeric_id_pattern = re.compile(r'"goods_id"\s*:\s*(\d{4,})', re.I)
            for match in numeric_id_pattern.finditer(html):
                product_id = match.group(1)
                if product_id in seen:
                    continue
                window = html[match.start():match.start() + 5000]
                name_match = name_pattern.search(window)
                if not name_match:
                    continue
                name = self._decode_json_string(name_match.group(1))
                price_match = price_pattern.search(window)
                price = price_match.group(1) if price_match else ""
                if name and not self.is_invalid_product_name(name) and not self.is_price_like(name):
                    products.append({
                        "name": name,
                        "price": f"${price}" if price else "",
                        "product_id": product_id,
                        "product_url": "",
                    })
                    seen.add(product_id)

        return self.dedupe_products(products)

    @staticmethod
    def _decode_json_string(value):
        try:
            return json.loads('"' + value + '"')
        except Exception:
            return value.replace('\\"', '"').replace('\\/', '/')

    # ------------------------------------------------------------
    # NETWORK
    # ------------------------------------------------------------

    async def extract_from_network(self):
        interceptor = getattr(self.page, "_pricing_interceptor", None)
        if interceptor is None:
            print("[NETWORK] No interceptor attached.")
            return []

        try:
            responses = interceptor.get_responses()
        except Exception as exc:
            print(f"[NETWORK] Cannot read responses: {exc!r}")
            return []

        if not responses:
            return []

        products = []
        for response in responses:
            try:
                body = response.get("body", "")
                if not body:
                    continue
                content_type = (response.get("content_type", "") or "").lower()
                if "json" not in content_type and not body.lstrip().startswith(("{", "[")):
                    continue
                data = json.loads(body)
                products.extend(self.walk_json_for_products(data))
            except Exception:
                continue

        normalized = self._normalize_many(products)
        return self.dedupe_products(normalized)

    def walk_json_for_products(self, value, depth=0):
        if depth > 12:
            return []
        results = []
        if isinstance(value, dict):
            if self.looks_like_product(value):
                results.append(self.product_from_json(value))
            for child in value.values():
                results.extend(self.walk_json_for_products(child, depth + 1))
        elif isinstance(value, list):
            for child in value:
                results.extend(self.walk_json_for_products(child, depth + 1))
        return results

    def looks_like_product(self, data):
        if not isinstance(data, dict):
            return False
        keys = {str(k).lower() for k in data}
        has_id = bool(keys & {"goods_id", "goodsid", "product_id", "productid"})
        has_name = bool(keys & {"goods_name", "goodsname", "product_name", "productname", "name", "title"})
        has_price = bool(keys & {"price", "sale_price", "saleprice", "current_price", "currentprice", "retail_price", "retailprice"})
        has_url = bool(keys & {"url", "product_url", "producturl", "goods_url", "goodsurl", "href"})
        # Do NOT treat generic `id` as a product ID. That was causing UI junk.
        return has_id and (has_name or has_price or has_url)

    def product_from_json(self, data):
        lowered = {str(k).lower(): v for k, v in data.items()}

        def first(keys):
            for key in keys:
                if key in data and data[key] is not None:
                    return data[key]
                if key.lower() in lowered and lowered[key.lower()] is not None:
                    return lowered[key.lower()]
            return ""

        product_id = first(["goods_id", "goodsId", "product_id", "productId"])
        name = first(["goods_name", "goodsName", "product_name", "productName", "name", "title"])
        price = first(["sale_price", "salePrice", "current_price", "currentPrice", "price", "retail_price", "retailPrice"])
        url = first(["product_url", "productUrl", "goods_url", "goodsUrl", "url", "href"])

        # Handle nested price objects such as salePrice: {amount: "16.62"}.
        if isinstance(price, dict):
            price = price.get("amount") or price.get("value") or ""

        return {
            "name": self.clean_text(name),
            "price": self.clean_text(price),
            "product_id": self.extract_id_from_value(product_id),
            "product_url": self.normalize_url(url),
        }

    # ------------------------------------------------------------
    # NORMALIZATION / MERGE
    # ------------------------------------------------------------

    def normalize_product(self, product):
        if not isinstance(product, dict):
            return None

        name = self.clean_text(product.get("name"))
        price = self.clean_text(product.get("price"))
        product_id = self.extract_id_from_value(product.get("product_id"))
        product_url = self.normalize_url(product.get("product_url"))

        if self.is_invalid_product_name(name) or self.is_price_like(name):
            name = ""

        if not product_id and product_url:
            product_id = self.extract_id_from_value(product_url)

        # Reject price-only UI fragments. A product needs a meaningful name
        # and/or an exact ID.
        if not name and not product_id:
            return None
        if not product_id and not name:
            return None
        if not name and not price and not product_id:
            return None

        return {
            "name": name,
            "price": price,
            "product_id": product_id,
            "product_url": product_url,
        }

    def merge_products(self, base_products, enrichment_products, source="network"):
        combined = [dict(p) for p in (base_products or []) if isinstance(p, dict)]

        def name_key(value):
            text = self.clean_text(value).lower()
            text = re.sub(r"[^a-z0-9]+", " ", text)
            return re.sub(r"\s+", " ", text).strip()

        def url_key(value):
            return (self.normalize_url(value) or "").rstrip("/").lower()

        for incoming in enrichment_products or []:
            if not isinstance(incoming, dict):
                continue

            inc_id = self.extract_id_from_value(incoming.get("product_id"))
            inc_url = url_key(incoming.get("product_url"))
            inc_name = name_key(incoming.get("name"))
            inc_price = self.clean_text(incoming.get("price"))
            matched = None

            # 1. Exact ID.
            if inc_id:
                for existing in combined:
                    if self.extract_id_from_value(existing.get("product_id")) == inc_id:
                        matched = existing
                        break

            # 2. Exact URL.
            if matched is None and inc_url:
                for existing in combined:
                    if url_key(existing.get("product_url")) == inc_url:
                        matched = existing
                        break

            # 3. Exact name. This is safe because it only enriches an
            # existing DOM/page-state record; it does not invent a new ID.
            if matched is None and inc_name:
                for existing in combined:
                    if name_key(existing.get("name")) == inc_name:
                        matched = existing
                        break

            if matched is not None:
                if inc_id and not self.extract_id_from_value(matched.get("product_id")):
                    matched["product_id"] = inc_id
                if inc_url and not matched.get("product_url"):
                    matched["product_url"] = inc_url
                if inc_price and not self.clean_text(matched.get("price")):
                    matched["price"] = inc_price
                if inc_name and not self.clean_text(matched.get("name")):
                    matched["name"] = self.clean_text(incoming.get("name"))
                continue

            # Embedded page state is trusted as a current-page product source.
            # Network is NOT allowed to create an ID-only record here unless
            # it has a meaningful name AND price.
            if source == "embedded":
                if inc_id and inc_name:
                    combined.append({
                        "name": self.clean_text(incoming.get("name")),
                        "price": inc_price,
                        "product_id": inc_id,
                        "product_url": inc_url,
                    })
            else:
                # IMPORTANT: network data can be unrelated recommendation/UI
                # data. Never create a new product from network-only records.
                # It may only enrich a product already present in the DOM or
                # current-page embedded state.
                continue

        return self.dedupe_products(combined)

    def _finalize_product(self, product):
        item = self.normalize_product(product)
        if not item:
            return None

        product_id = item.get("product_id", "")
        if product_id and not item.get("product_url"):
            item["product_url"] = self.build_product_url(product_id)

        # For ClickHouse, don't pass obviously invalid prices.
        if item.get("price") and not self.has_valid_money(item["price"]):
            item["price"] = ""

        return item

    def dedupe_products(self, products):
        unique = []
        seen_ids = set()
        seen_urls = set()
        seen_names = set()

        for product in products or []:
            if not isinstance(product, dict):
                continue

            item = self.normalize_product(product)
            if not item:
                continue

            name = item["name"]
            price = item["price"]
            product_id = item["product_id"]
            product_url = item["product_url"]

            if product_id and not product_url:
                product_url = self.build_product_url(product_id)

            if product_id and product_id in seen_ids:
                # If an earlier record has no price, enrich it with this one.
                for old in unique:
                    if old.get("product_id") == product_id:
                        if not old.get("price") and price:
                            old["price"] = price
                        if not old.get("name") and name:
                            old["name"] = name
                        if not old.get("product_url") and product_url:
                            old["product_url"] = product_url
                        break
                continue

            url_key = product_url.rstrip("/").lower() if product_url else ""
            if url_key and url_key in seen_urls:
                continue

            name_key = re.sub(r"\s+", " ", name).strip().lower() if name else ""
            if name_key and len(name_key) > 5 and not product_id and name_key in seen_names:
                continue

            record = {
                "name": name,
                "price": price,
                "product_id": product_id,
                "product_url": product_url,
            }
            unique.append(record)

            if product_id:
                seen_ids.add(product_id)
            if url_key:
                seen_urls.add(url_key)
            if name_key and not product_id:
                seen_names.add(name_key)

        return unique

    # ------------------------------------------------------------
    # ID / URL / TEXT / PRICE HELPERS
    # ------------------------------------------------------------

    def extract_id_from_value(self, value):
        if value is None:
            return ""
        text = str(value).strip()
        if not text:
            return ""

        m = re.search(r"-p-(\d{4,})(?:\.html)?", text, re.I)
        if m:
            return m.group(1)

        try:
            params = parse_qs(urlparse(text).query)
            for key in ["goods_id", "goodsId", "product_id", "productId"]:
                vals = params.get(key)
                if vals and re.fullmatch(r"\d{4,}", str(vals[0]).strip()):
                    return str(vals[0]).strip()
        except Exception:
            pass

        m = re.search(
            r"(?:goods[_-]?id|goodsId|product[_-]?id|productId)\s*[=:\"']+\s*(\d{4,})",
            text,
            re.I,
        )
        if m:
            return m.group(1)

        m = re.search(r"(?:goods|product)[_-]?(\d{5,})", text, re.I)
        if m:
            return m.group(1)

        if re.fullmatch(r"\d{5,}", text):
            return text
        return ""

    def normalize_url(self, value):
        if value is None:
            return ""
        url = str(value).strip()
        if not url:
            return ""
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = "https://us.shein.com" + url

        if re.search(r"-p-\d{4,}|/product(?:-detail)?/", url, re.I):
            return url

        product_id = self.extract_id_from_value(url)
        return self.build_product_url(product_id) if product_id else ""

    def build_product_url(self, product_id):
        product_id = self.extract_id_from_value(product_id)
        return f"https://us.shein.com/--p-{product_id}.html" if product_id else ""

    def clean_text(self, value):
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            try:
                value = json.dumps(value, ensure_ascii=False)
            except Exception:
                value = str(value)
        return re.sub(r"\s+", " ", str(value)).strip()

    def is_invalid_product_name(self, value):
        text = self.clean_text(value)
        if not text:
            return False
        lowered = text.lower()
        exact = {
            "banner", "strictly necessary cookies", "performance cookies",
            "functional cookies", "targeting cookies", "social media cookies",
            "swiss franc", "mexican peso", "euro", "pound sterling",
            "canadian dollar", "us dollar",
        }
        if lowered in exact:
            return True
        patterns = [
            r"^image_component_\d+$",
            r"^image_carousel_component_\d+$",
            r"^pc下载",
            r"^cookie", r"^cookies", r"^accept cookies",
            r"^privacy", r"^terms",
        ]
        return any(re.search(p, lowered, re.I) for p in patterns)

    def is_price_like(self, value):
        text = self.clean_text(value)
        return bool(re.fullmatch(
            r"(?:[$€£]\s*\d+(?:[.,]\d{1,2})?|(?:USD|EUR|GBP)\s*\d+(?:[.,]\d{1,2})?)",
            text,
            re.I,
        )) if text else False

    def is_numeric_price(self, value):
        try:
            number = float(str(value).replace(",", "."))
            return 0 < number < 1000000
        except Exception:
            return False

    def has_valid_money(self, value):
        text = self.clean_text(value)
        return bool(re.search(
            r"(?:[$€£]\s*\d+(?:[.,]\d{1,2})?|\b(?:USD|EUR|GBP)\s*\d+(?:[.,]\d{1,2})?)",
            text,
            re.I,
        ))
