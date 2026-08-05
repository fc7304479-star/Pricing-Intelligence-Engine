import random


class ProxyManager:

    def __init__(self):

        self.proxies = [

            # HTTP
            None,

            # Examples
            # "http://username:password@ip:port",
            # "http://ip:port",

        ]

    def get_proxy(self):

        return random.choice(self.proxies)