from __future__ import print_function

import ConfigParser
import requests
import bs4
import sys

default_config_file = 'conf/config.ini'

config = ConfigParser.ConfigParser()
assert isinstance(config, ConfigParser.ConfigParser)

config.read(default_config_file)


YES24_LOGIN_URL = "https://www.yes24.com/Templates/FTLogIn.aspx"
YES24_CART_URL = "http://ssl.yes24.com/Cart/Cart"

ALADIN_LOGIN_URL = "https://www.aladin.co.kr/login/wlogin_popup.aspx"
ALADIN_ADD_CART_BY_ISBN_URL = "http://www.aladin.co.kr/shop/BasketAjax.aspx?method=BasketAdd&isbn={ISBN}"


def login_into_yes24(id, password):
    print("id: {id}, password: {password}".format(id=id, password=password))

    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=4,
                                            pool_maxsize=4,
                                            max_retries=3)
    sess.mount('https://', adapter)

    r = sess.post(url=YES24_LOGIN_URL, data={
        'LoginType': '',
        'FBLoginSub$ReturnURL': '',
        'FBLoginSub$ReturnParams': '',
        'RefererUrl': 'http://www.yes24.com/Main/Default.aspx',
        'AutoLogin': 1,
        'LoginIDSave': 'N',
        'FBLoginSub$NaverCode': '',
        'FBLoginSub$NaverState': '',
        'SMemberID': id,
        'SMemberPassword': password,
    })

    assert isinstance(r, requests.Response)
    if r.status_code != requests.codes.ok:
        raise Exception('Fail to login')
    r.close()

    r = sess.get(url=YES24_CART_URL)

    assert isinstance(r, requests.Response)
    if r.status_code != requests.codes.ok:
        raise Exception('Fail to get cart page')

    doc = bs4.BeautifulSoup(markup=r.text, from_encoding='utf-8')

    r.close()

    cart_elements = doc.select("#divNormalCart > table td.le a.pd_a")
    after_order_elements = doc.select("#divTabAfterOrderGoodsPage div.goods_info > p.goods_name > a")

    cart_items = map(lambda elem: {'url': elem['href'], 'title': elem.text}, cart_elements)
    after_order_items = map(lambda elem: {'url': elem['href'], 'title': elem.text}, after_order_elements)

    for item in cart_items + after_order_items:
        yield item


def login_into_aladin(id, password):
    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=4,
                                            pool_maxsize=4,
                                            max_retries=3)
    sess.mount('https://', adapter)

    r = sess.post(url=ALADIN_LOGIN_URL, data={'Email': id, 'Password': password, 'Action': 1, 'SecureLogin': False})
    print(sess.cookies)

    assert isinstance(r, requests.Response)
    if r.status_code != requests.codes.ok:
        raise Exception('Fail to login')
    r.close()

    return sess

    #sess.get(url=ALADIN_ADD_CART_BY_ISBN_URL.format(ISBN=))


def add_to_aladin_cart(sess, item):
    url = ALADIN_ADD_CART_BY_ISBN_URL.format(ISBN=item['isbn'])
    print(url)
    r = sess.get(url=url)
    assert isinstance(r, requests.Response)
    if r.status_code != requests.codes.ok:
        raise Exception('Fail to login')
    r.close()


def append_isbn(item):
    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=4,
                                            pool_maxsize=4,
                                            max_retries=3)
    sess.mount('https://', adapter)

    r = sess.get(url=item['url'])

    assert isinstance(r, requests.Response)
    if r.status_code != requests.codes.ok:
        raise Exception('Fail to get cart page')

    doc = bs4.BeautifulSoup(markup=r.text, from_encoding='utf-8')

    r.close()

    isbn_elem = doc.select("#salsInfo dd.isbn10 > p")

    if len(isbn_elem) == 0:
        print("not found isbn: {}".format(item['url']))
        raise Exception("not found isbn: {}".format(item['url']))
    isbn = isbn_elem[0].text

    item['isbn'] = isbn
    return item


def main(args):
    yes24_iter = login_into_yes24(id=config.get('yes24', 'id'),
                                  password=config.get('yes24', 'password'))
    sess = login_into_aladin(id=config.get('aladin', 'id'),
                             password=config.get('aladin', 'password'))

    for item in yes24_iter:
        add_to_aladin_cart(sess, append_isbn(item))


if __name__ == '__main__':
    main(sys.argv)
