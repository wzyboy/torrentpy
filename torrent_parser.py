#!/usr/bin/env python

import re
import sys
import json
from collections import OrderedDict


class TorrentParser(object):

    INT_START = b'i'
    INT_RE = re.compile(b'i(\d+)e')
    STR_START = re.compile(b'\d+(?=:)')
    LIST_START = b'l'
    DICT_START = b'd'
    END = b'e'

    def __init__(self, raw_torrent):
        self.raw_torrent = raw_torrent
        self.cursor = 0

    def get_remainder(self):
        remainder = self.raw_torrent[self.cursor:]
        return remainder

    def parse_int(self):
        print('parse int')
        remainder = self.get_remainder()
        matched = self.INT_RE.match(remainder)
        matched_int = int(matched.group(1))
        self.cursor += len(matched.group(1)) + 2
        print('parsed int: {}'.format(matched_int))
        return matched_int

    def parse_str(self):
        print('parse str')
        remainder = self.get_remainder()
        matched = self.STR_START.match(remainder)
        str_len = int(matched.group(0))
        str_start_pos = self.cursor + len(matched.group(0)) + 1
        str_end_pos = str_start_pos + str_len
        string = self.raw_torrent[str_start_pos:str_end_pos]
        self.cursor = str_end_pos
        if str_len > 100:
            string = b'CONTENT_TOO_LONG'
        decoded_string = string.decode('utf-8', errors='ignore')
        print('parsed string: {}'.format(decoded_string))
        return decoded_string

    def try_next(self):
        print('try next')
        remainder = self.get_remainder()
        if remainder[0:1] == self.INT_START:
            print('next is int')
            item = self.parse_int()
            return item
        elif self.STR_START.match(remainder):
            print('next is str')
            item = self.parse_str()
            return item
        elif remainder[0:1] == self.LIST_START:
            print('next is list')
            self.cursor += 1
            item = self.parse_list()
            return item
        elif remainder[0:1] == self.DICT_START:
            print('next is dict')
            self.cursor += 1
            item = self.parse_dict()
            return item
        elif remainder[0:1] == b'e':
            print('next is END')
            self.cursor += 1
            return None
        else:
            raise ValueError('Unknown next item: {}'.format(remainder[0:1]))

    def parse_list(self):
        print('parse list')
        parsed_list = []
        while True:
            next_item = self.try_next()
            if next_item is None:
                break
            else:
                parsed_list.append(next_item)
        return parsed_list

    def parse_dict(self):
        print('parse dict')
        dict_list = []
        while True:
            next_item = self.try_next()
            if next_item is None:
                break
            else:
                dict_list.append(next_item)
        parsed_dict = OrderedDict(
            (dict_list[i], dict_list[i + 1])
            for
            i in range(0, len(dict_list), 2)
        )
        return parsed_dict

    def parse(self):
        print('start parse')
        if self.raw_torrent[0:1] != self.DICT_START:
            raise ValueError('Not a torrent file')
        else:
            self.cursor += 1
        parsed_torrent = self.parse_dict()
        return parsed_torrent


def main():
    filename = sys.argv[1]
    raw_torrent = open(filename, 'rb').read()
    torrent_parser = TorrentParser(raw_torrent)
    parsed_torrent = torrent_parser.parse()
    print(json.dumps(parsed_torrent, indent=2))


if __name__ == '__main__':
    main()
