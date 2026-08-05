import re


class HTMLCleaner:

    def clean(self, html):

        html = re.sub(
            r"<script.*?</script>",
            "",
            html,
            flags=re.S,
        )

        html = re.sub(
            r"<style.*?</style>",
            "",
            html,
            flags=re.S,
        )

        html = re.sub(
            r"\s+",
            " ",
            html,
        )

        return html