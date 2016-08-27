# coding=utf-8
import bs4
import re
import requests

from bookstore_accessor import BookstoreAccessor, BookItem


class Yes24Accessor(BookstoreAccessor):
    LOGIN_URL = "https://www.yes24.com/Templates/FTLogIn.aspx"
    CART_URL = "http://ssl.yes24.com/Cart/Cart"
    ADD_CART_BY_GOODS_NO = "http://www.yes24.com/24/Order/CheckOrderGoods?goodsNos={goods_no}&checkOption=N&isMyList=false"
    ADD_CART = "http://www.yes24.com/24/Content/AjaxPage/Cart/Cart.ashx?CategoryNumber=001001003022019&Pcode=001"
    SEARCH_URL = "http://www.yes24.com/searchcorner/Search?domain=BOOK&query={query}"

    def __init__(self):
        BookstoreAccessor.__init__(self)

    def login(self, login_id, password):
        print("id: {id}, password: {password}".format(id=login_id, password=password))

        r = self.sess.post(
            url=self.LOGIN_URL,
            headers={
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
            },
            data={
                'LoginType': '',
                'FBLoginSub$ReturnURL': '',
                'FBLoginSub$ReturnParams': '',
                'RefererUrl': 'http://www.yes24.com/Main/Default.aspx',
                'AutoLogin': 1,
                'LoginIDSave': 'N',
                'FBLoginSub$NaverCode': '',
                'FBLoginSub$NaverState': '',
                'SMemberID': login_id,
                'SMemberPassword': password,
            }
        )

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to login')
        r.close()

    def search(self, query):
        r = self.sess.get(url=self.SEARCH_URL.format(query=query))

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to get cart page')

        doc = bs4.BeautifulSoup(markup=r.text, from_encoding='utf-8')

        r.close()

        search_items = doc.select(
            "#schMid_wrap > div:nth-of-type(3) > div.goodsList.goodsList_list > table > tr > td.goods_infogrp > p.goods_name.goods_icon > a")
        book_items = map(lambda elem: BookItem(url=elem['href'], title=elem.text), search_items)
        return book_items

    def iterator(self):
        r = self.sess.get(url=self.CART_URL)

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to get cart page')

        doc = bs4.BeautifulSoup(markup=r.text, from_encoding='utf-8')

        r.close()

        cart_elements = doc.select("#divNormalCart > table td.le a.pd_a")
        after_order_elements = doc.select("#divTabAfterOrderGoodsPage div.goods_info > p.goods_name > a")

        cart_items = map(lambda elem: BookItem(url=elem['href'], title=elem.text), cart_elements)
        after_order_items = map(lambda elem: BookItem(url=elem['href'], title=elem.text), after_order_elements)

        for item in cart_items + after_order_items:
            yield item

    @staticmethod
    def extract_goods_no_from_url(url):
        m = re.match(".+/(?P<no>\d+)", url)
        return m.group('no')

    """
    def add(self, item):
        search_book_items = self.search(item.isbn)
        if len(search_book_items) == 0:
            raise Exception('Not found: ' + item)

        print(u"searched in yes24: title: {title}".format(title=search_book_items[0].title))

        target_item = search_book_items[0]
        assert isinstance(target_item, BookItem)
        target_goods_no = self.extract_goods_no_from_url(target_item.url)
        print(u"target goods no: {no}".format(no=target_goods_no))

        r = self.sess.post(url=self.ADD_CART_BY_GOODS_NO.format(goods_no=target_goods_no))

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to add cart')
        r.close()
    """

    def add(self, item):
        search_book_items = self.search(item.isbn)
        if len(search_book_items) == 0:
            raise Exception('Not found: ' + item)

        print(u"searched in yes24: title: {title}".format(title=search_book_items[0].title))

        target_item = search_book_items[0]
        assert isinstance(target_item, BookItem)
        target_goods_no = self.extract_goods_no_from_url(target_item.url)
        print(u"target goods no: {no}".format(no=target_goods_no))

        self._add_by_goods_no(goods_no=target_goods_no)

    def _add_by_goods_no(self, goods_no):
        # cookie에 ServiceCookie 또는 CartNo 가 있으면 들어간다.
        r = self.sess.post(
            url=self.ADD_CART,
            headers={
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
                'Referer': 'http://www.yes24.com/24/Goods/{goods_no}'.format(goods_no=goods_no),
            },
            data={'CART_GOODS_INFO': u"1{backspace}{goods_no}{backspace}1{backspace}{bell}".format(goods_no=goods_no, backspace=u"\u0008", bell=u"\u0007")}
            #data={'CART_GOODS_INFO': u"1{backspace}{goods_no}{backspace}1{backspace}{bell}".format(goods_no=goods_no, backspace=u"\x08", bell=u"\x07")} # Same Above
            #data={'CART_GOODS_INFO': "1%08{goods_no}%081%08%07".format(goods_no=goods_no)}  # Also same above thems
        )

        assert isinstance(r, requests.Response)
        print("response: {}".format(r.content))
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to add cart')
        r.close()

    def append_isbn(self, item):
        assert isinstance(item, BookItem)

        r = self.sess.get(url=item.url)

        assert isinstance(r, requests.Response)
        if r.status_code != requests.codes.ok:
            raise Exception('Fail to get cart page')

        doc = bs4.BeautifulSoup(markup=r.text, from_encoding='utf-8')

        r.close()

        isbn_elem = doc.select("#salsInfo dd.isbn10 > p")

        if len(isbn_elem) == 0:
            print("not found isbn: {}".format(item.url))
            raise Exception("not found isbn: {}".format(item.url))
        isbn = isbn_elem[0].text

        item.isbn = isbn
        return item
