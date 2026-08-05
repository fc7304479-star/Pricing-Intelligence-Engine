from .layout_detector import LayoutDetector


class SelfHealing:

    def repair(self, html):

        detector = LayoutDetector(html)

        return {

            "title": detector.product_title(),

            "price": detector.product_price()

        }