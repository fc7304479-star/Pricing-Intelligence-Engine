import json
from pathlib import Path


class SelectorCache:

    def __init__(self):

        self.file = Path(
            "output/selector_cache.json"
        )

        self.file.parent.mkdir(
            exist_ok=True
        )

    def save(
        self,
        failed,
        fixed,
    ):

        data = {}

        if self.file.exists():

            try:

                data = json.loads(
                    self.file.read_text()
                )

            except Exception:

                data = {}

        data[failed] = fixed

        self.file.write_text(

            json.dumps(
                data,
                indent=4,
            )

        )

    def get(self, failed):

        if not self.file.exists():

            return None

        try:

            data = json.loads(
                self.file.read_text()
            )

            return data.get(failed)

        except Exception:

            return None