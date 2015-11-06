#!/usr/bin/env python

import re
import sys
import json
from binascii import hexlify
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
        remainder = self.get_remainder()
        matched = self.INT_RE.match(remainder)
        matched_int = int(matched.group(1))
        self.cursor += len(matched.group(1)) + 2
        return matched_int

    def parse_str(self):
        remainder = self.get_remainder()
        matched = self.STR_START.match(remainder)
        str_len = int(matched.group(0))
        str_start_pos = self.cursor + len(matched.group(0)) + 1
        str_end_pos = str_start_pos + str_len
        string = self.raw_torrent[str_start_pos:str_end_pos]
        self.cursor = str_end_pos
        try:
            decoded_string = string.decode('utf-8')
        except UnicodeDecodeError:  # hash_list
            return string
        return decoded_string

    def try_next(self):
        remainder = self.get_remainder()
        if remainder[0:1] == self.INT_START:
            item = self.parse_int()
            return item
        elif self.STR_START.match(remainder):
            item = self.parse_str()
            return item
        elif remainder[0:1] == self.LIST_START:
            self.cursor += 1
            item = self.parse_list()
            return item
        elif remainder[0:1] == self.DICT_START:
            self.cursor += 1
            item = self.parse_dict()
            return item
        elif remainder[0:1] == b'e':
            self.cursor += 1
            return None
        else:
            raise ValueError('Unknown next item: {}'.format(remainder[0:1]))

    def parse_list(self):
        parsed_list = []
        while True:
            next_item = self.try_next()
            if next_item is None:
                break
            else:
                parsed_list.append(next_item)
        return parsed_list

    def parse_dict(self):
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
        if self.raw_torrent[0:1] != self.DICT_START:
            raise ValueError('Not a torrent file')
        else:
            self.cursor += 1
        parsed_torrent = self.parse_dict()
        pieces = parsed_torrent['info']['pieces']
        hash_list = [
            hexlify(pieces[i:i + 20]).decode('utf-8')
            for
            i in range(0, len(pieces), 20)
        ]
        parsed_torrent['info']['pieces'] = hash_list
        return parsed_torrent


def main():
    try:
        filename = sys.argv[1]
    except IndexError:
        raise SystemExit('Usage: {} [torrent]'.format(__file__))
    raw_torrent = open(filename, 'rb').read()
    torrent_parser = TorrentParser(raw_torrent)
    parsed_torrent = torrent_parser.parse()
    print(json.dumps(parsed_torrent, indent=2))


if __name__ == '__main__':
    main()
