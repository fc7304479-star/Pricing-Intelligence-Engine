class NetworkInterceptor:

    def __init__(self):
        self.responses = []

    async def attach(self, page):

        async def handle_response(response):

            try:

                if response.request.resource_type != "xhr":
                    return

                body = await response.text()

                self.responses.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "body": body,
                    }
                )

                print(
                    f"[NETWORK] {response.status} {response.url}"
                )

            except Exception:
                pass

        page.on("response", handle_response)

    def get_responses(self):
        return self.responses