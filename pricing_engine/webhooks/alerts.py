import requests


class Webhook:

    def send(self, url, payload):

        try:

            requests.post(url, json=payload, timeout=10)

            print("Webhook Sent")

        except Exception as e:

            print(e)