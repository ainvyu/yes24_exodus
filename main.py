from __future__ import print_function

import ConfigParser
import sys

from lib.yes24 import Yes24Accessor
from lib.aladin import AladinAccessor

default_config_file = 'conf/config.ini'

config = ConfigParser.ConfigParser()
assert isinstance(config, ConfigParser.ConfigParser)

config.read(default_config_file)


def main(args):
    yes24_accessor = Yes24Accessor()
    yes24_accessor.login(login_id=config.get('yes24', 'id'),
                         password=config.get('yes24', 'password'))
    aladin_accessor = AladinAccessor()
    aladin_accessor.login(login_id=config.get('aladin', 'id'),
                          password=config.get('aladin', 'password'))

    for item in aladin_accessor.iterator():
        item_with_isbn = aladin_accessor.append_isbn(item)
        print(u"title: {title}".format(title=item_with_isbn.title))
        yes24_accessor.add(item_with_isbn)


if __name__ == '__main__':
    main(sys.argv)
