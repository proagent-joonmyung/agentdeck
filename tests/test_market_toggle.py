import unittest

from market import Quote
from pages import page_market


class MarketToggleTest(unittest.TestCase):
    def test_press_swaps_percent_and_price(self):
        q = [Quote("삼성전자", 2.6, "71,200")]
        self.assertEqual((page_market("top", q)[0].title, page_market("top", q)[0].sub), ("+2.60%", "71,200"))
        b = page_market("top", q, show_price=True)[0]
        self.assertEqual((b.title, b.sub), ("71,200", "+2.60%"))


if __name__ == "__main__":
    unittest.main()
