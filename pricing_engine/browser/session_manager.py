import json
from pathlib import Path


class SessionManager:

    SESSION_FILE = Path("session.json")

    @classmethod
    async def load(cls, context):

        if not cls.SESSION_FILE.exists():
            return

        try:

            cookies = json.loads(
                cls.SESSION_FILE.read_text(
                    encoding="utf-8"
                )
            )

            await context.add_cookies(cookies)

            print(
                f"[SESSION] Loaded {len(cookies)} cookies"
            )

        except Exception as e:

            print(e)

    @classmethod
    async def save(cls, context):

        try:

            cookies = await context.cookies()

            cls.SESSION_FILE.write_text(

                json.dumps(
                    cookies,
                    indent=4
                ),

                encoding="utf-8"

            )

            print(
                f"[SESSION] Saved {len(cookies)} cookies"
            )

        except Exception as e:

            print(e)