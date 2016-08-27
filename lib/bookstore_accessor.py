import requests

class BookstoreAccessor:
    def __init__(self):
        self.sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=1,
                                                pool_maxsize=1,
                                                max_retries=3)
        self.sess.mount('https://', adapter)

    def login(self, login_id, password):
        pass

    def iterator(self):
        pass

    def add(self, item):
        pass

    def append_isbn(self, item):
        pass


class BookItem:
    def __init__(self, url, title, isbn=None):
        self.url = url
        self.title = title
        self.isbn = isbn