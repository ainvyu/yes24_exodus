# coding=utf-8

import math
import re

import bs4
import requests

from bookstore_accessor import BookstoreAccessor, BookItem


class AladinAccessor(BookstoreAccessor):
    LOGIN_URL = "https://www.aladin.co.kr/login/wlogin_popup.aspx"
    CART_URL = "http://www.aladin.co.kr/shop/wbasket.aspx"
    ARCHIVE_URL = "http://www.aladin.co.kr/shop/wsafebasket.aspx"
    ADD_CART_BY_ISBN_URL = "http://www.aladin.co.kr/shop/BasketAjax.aspx?method=BasketAdd&isbn={ISBN}"
    ARCHIVE_PAGE_ITEM_COUNT = 48

    def __init__(self):
        BookstoreAccessor.__init__(self)

    def login(self, login_id, password):
        r = self.sess.post(
            url=self.LOGIN_URL,
            data={'Email': login_id, 'Password': password, 'Action': 1, 'SecureLogin': False}
        )
        print(self.sess.cookies)

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to login')
        r.close()

    def get_cart_items(self):
        r = self.sess.get(url=self.CART_URL)

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to get cart page')

        doc = bs4.BeautifulSoup(markup=r.text, from_encoding='utf-8')

        r.close()

        cart_elements = doc.select(".CartTr > td:nth-of-type(1) > a")
        return map(lambda elem: BookItem(url=elem['href'], title=elem['title']), cart_elements)

    def _get_after_order_item_page(self, page, count=ARCHIVE_PAGE_ITEM_COUNT):
        r = self.sess.post(url=self.ARCHIVE_URL, data={
            'page': page,
            'BranchType': 0,
            'SearchWord': '',
            'ViewType': 'Simple',
            'ViewRowsCount': count,
            'SortOrder': 1,
            'IsBuyGoods': 'False',
            'IsNotBuyGoods': 'False',
            'IsDCFree': 'False',
            'HasStock': 'False',
            'NotHasStock': 'False',
            'HasUsedType': 0,
            'HasEventType': 0,
        })

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to get cart page')

        html = r.text
        r.close()

        return html

    def _get_after_order_item_page_doc(self, page, count=ARCHIVE_PAGE_ITEM_COUNT):
        html = self._get_after_order_item_page(page, count)

        #correction_html = r.text.replace('width="85" border="0"></a></td>', 'width="85" border="0"></a></td></tr>').replace(u'점</span>', '')
        #codecs.open('correction.html', 'w', 'utf-8').write(correction_html)
        #doc = bs4.BeautifulSoup(correction_html, 'html.parser', from_encoding='utf-8')

        return bs4.BeautifulSoup(html, 'html5lib')

    def get_after_order_items(self):
        first_page_doc = self._get_after_order_item_page_doc(1, self.ARCHIVE_PAGE_ITEM_COUNT)

        archive_count = float(first_page_doc.select('.search_t_g > span')[0].text)
        after_order_items = []
        for i in range(1, int(math.ceil(archive_count/self.ARCHIVE_PAGE_ITEM_COUNT)+1)):
            doc = self._get_after_order_item_page_doc(i, self.ARCHIVE_PAGE_ITEM_COUNT)

            links = doc.find_all('a')
            target_href_prefix = 'http://www.aladin.co.kr/shop/wproduct.aspx?ItemId='
            after_order_items_in_this_page = map(lambda item: BookItem(url=item[0], title=item[1]),
                                                 dict(
                                                     filter(lambda item: item[0].startswith(target_href_prefix),
                                                            map(lambda link: (link['href'], link.text), links)
                                                            )
                                                 ).items()
                                                 )

            after_order_items.extend(after_order_items_in_this_page)

        return after_order_items

    def iterator(self):
        cart_items = self.get_cart_items()
        after_order_items = self.get_after_order_items()

        for item in cart_items + after_order_items:
            yield item

    def add(self, item):
        assert isinstance(item, BookItem)

        url = self.ADD_CART_BY_ISBN_URL.format(ISBN=item.isbn)
        print(url)
        r = self.sess.get(url=url)
        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to login')
        r.close()

    def append_isbn(self, item):
        assert isinstance(item, BookItem)

        r = self.sess.get(url=item.url)

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to get cart page')

        doc = bs4.BeautifulSoup(markup=r.text, from_encoding='utf-8')

        r.close()

        isbn_elem = doc.select("meta[property=og:barcode]")

        if len(isbn_elem) == 0:
            print("not found isbn: {}".format(item.url))
            raise Exception("not found isbn: {}".format(item.url))
        isbn = isbn_elem[0]['content']

        item.isbn = isbn
        return item


