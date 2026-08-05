import random


USER_AGENTS = [

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/137.0 Safari/537.36",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36",

]


VIEWPORTS = [

    {"width":1920,"height":1080},

    {"width":1600,"height":900},

    {"width":1366,"height":768},

    {"width":1536,"height":864},

]


LOCALES = [

    "en-US",
    "en-GB",
]


TIMEZONES = [

    "America/New_York",

    "America/Chicago",

    "America/Los_Angeles",

]


class Fingerprint:

    @staticmethod
    def random_user_agent():

        return random.choice(USER_AGENTS)

    @staticmethod
    def random_viewport():

        return random.choice(VIEWPORTS)

    @staticmethod
    def random_locale():

        return random.choice(LOCALES)

    @staticmethod
    def random_timezone():

        return random.choice(TIMEZONES)