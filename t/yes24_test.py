import unittest
from lib.yes24 import Yes24Accessor


class MyTestCase(unittest.TestCase):
    def test_something(self):
        goods_no = Yes24Accessor.extract_goods_no_from_url('/24/goods/30297264?scode=032&amp;OzSrank=1')
        self.assertEqual(30297264, int(goods_no))


if __name__ == '__main__':
    unittest.main()
