import json
from pathlib import Path


class NetworkInterceptor:

    def __init__(self):

        self.responses = []

    # =========================================================
    # ATTACH
    # =========================================================

    async def attach(
        self,
        page
    ):

        # Keep responses accessible from the page.

        page._pricing_network_responses = (
            self.responses
        )

        # Keep the SAME interceptor object accessible
        # from the page.

        page._pricing_interceptor = self

        # =====================================================
        # RESPONSE HANDLER
        # =====================================================

        async def handle_response(
            response
        ):

            try:

                resource_type = (
                    response.request.resource_type
                )

                # Only capture XHR and FETCH.

                if resource_type not in (
                    "xhr",
                    "fetch"
                ):

                    return

                # =================================================
                # CONTENT TYPE
                # =================================================

                content_type = (
                    response.headers.get(
                        "content-type",
                        ""
                    )
                    .lower()
                )

                # Only capture JSON responses.

                if "json" not in content_type:

                    return

                # =================================================
                # RESPONSE BODY
                # =================================================

                body = await response.text()

                if not body:

                    return

                # =================================================
                # RECORD
                # =================================================

                record = {

                    "url": response.url,

                    "status": response.status,

                    "resource_type": resource_type,

                    "content_type": content_type,

                    "body": body,
                }

                self.responses.append(
                    record
                )

                print(
                    f"[NETWORK] "
                    f"{response.status} "
                    f"{resource_type.upper()} "
                    f"{response.url}"
                )

            except Exception as e:

                print(
                    f"[NETWORK ERROR] "
                    f"{repr(e)}"
                )

        # =====================================================
        # REGISTER LISTENER
        # =====================================================

        page.on(
            "response",
            handle_response
        )

        print(
            "[NETWORK] Interceptor attached"
        )

    # =========================================================
    # GET RESPONSES
    # =========================================================

    def get_responses(
        self
    ):

        return self.responses

    # =========================================================
    # SAVE
    # =========================================================

    def save(
        self,
        path="output/network.json"
    ):

        output_path = Path(
            path
        )

        # Create output directory.

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Write JSON.

        with output_path.open(
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.responses,
                f,
                ensure_ascii=False,
                indent=2
            )

        print(
            f"[NETWORK] Saved "
            f"{len(self.responses)} responses -> "
            f"{output_path}"
        )