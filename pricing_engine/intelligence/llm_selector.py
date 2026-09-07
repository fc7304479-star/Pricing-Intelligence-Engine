import os
import re

from dotenv import load_dotenv
from google import genai


load_dotenv()


class LLMSelector:

    """
    Gemini-powered selector discovery.

    The LLM receives HTML and suggests
    a CSS selector for product pricing.
    """

    def __init__(self):

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = "gemini-2.5-flash"

    # ========================================================
    # FIND PRICE SELECTOR
    # ========================================================

    def find_price_selector(
        self,
        html: str
    ):

        if not html:

            return None

        # Prevent sending enormous HTML to LLM.
        html = html[:50000]

        prompt = f"""
You are an expert web scraping engineer.

You are given HTML from an ecommerce page.

Identify the best CSS selector that points
to the product price.

Rules:

1. Return ONLY one CSS selector.
2. No explanation.
3. No markdown.
4. No code block.
5. No extra text.

HTML:

{html}
"""

        try:

            response = self.client.models.generate_content(

                model=self.model,

                contents=prompt,
            )

            selector = (
                response.text
                if response.text
                else ""
            )

            selector = selector.strip()

            # Remove markdown fences.
            selector = selector.replace(
                "```css",
                ""
            )

            selector = selector.replace(
                "```",
                ""
            )

            selector = selector.strip()

            # Remove quotes.
            selector = selector.strip(
                "\"'"
            )

            print(
                f"[LLM] Suggested Selector -> "
                f"{selector}"
            )

            return selector

        except Exception as e:

            print(
                f"[LLM ERROR] {e}"
            )

            return None