#!/usr/bin/env python

import sys
import json
from binascii import unhexlify
from operator import add
from functools import reduce
from collections import OrderedDict


class TorrentComposer(object):

    INT_TPL = 'i{}e'
    STR = (str, bytes) if sys.version_info.major == 3 else basestring  # NOQA
    STR_SEP = b':'
    LIST_START = b'l'
    DICT_START = b'd'
    END = b'e'

    def __init__(self, parsed_torrent):
        self.parsed_torrent = parsed_torrent
        self.raw_torrent = b''

    def compose_int(self, integer):
        composed_int = self.INT_TPL.format(integer).encode('utf-8')
        return composed_int

    def compose_str(self, string):
        try:
            bin_str = string.encode('utf-8')
        except (AttributeError, UnicodeDecodeError):  # hash_list
            bin_str = string
        composed_str = b''
        composed_str += str(len(bin_str)).encode('utf-8')
        composed_str += self.STR_SEP
        composed_str += bin_str
        return composed_str

    def try_next(self, item):
        if isinstance(item, int):
            composed_int = self.compose_int(item)
            return composed_int
        elif isinstance(item, self.STR):
            composed_str = self.compose_str(item)
            return composed_str
        elif isinstance(item, list):
            composed_list = self.compose_list(item)
            return composed_list
        elif isinstance(item, dict):
            composed_dict = self.compose_dict(item)
            return composed_dict
        else:
            raise ValueError('Unknown next item: {}'.format(item))

    def compose_list(self, list_):
        composed_list = b''
        composed_list += self.LIST_START
        iterator = iter(list_)
        while True:
            try:
                next_item = next(iterator)
            except StopIteration:
                composed_list += self.END
                break
            composed = self.try_next(next_item)
            composed_list += composed
        return composed_list

    def compose_dict(self, dict_):
        composed_dict = b''
        composed_dict += self.DICT_START
        flatten_dict = list(reduce(add, dict_.items()))
        iterator = iter(flatten_dict)
        while True:
            try:
                next_item = next(iterator)
            except StopIteration:
                composed_dict += self.END
                return composed_dict
            composed = self.try_next(next_item)
            composed_dict += composed
        return composed_dict

    def compose(self):
        if not isinstance(self.parsed_torrent, dict):
            raise ValueError('Not a parsed torrent')
        hash_list = self.parsed_torrent['info']['pieces']
        pieces = b''.join([
            unhexlify(h)
            for
            h in hash_list
        ])
        self.parsed_torrent['info']['pieces'] = pieces
        composed_torrent = self.compose_dict(self.parsed_torrent)
        return composed_torrent


def main():
    try:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    except IndexError:
        raise SystemExit('Usage: {} [json] [torrent]'.format(__file__))
    parsed_torrent = json.load(open(input_file, 'r'), object_pairs_hook=OrderedDict)
    torrent_composer = TorrentComposer(parsed_torrent)
    composed_torrent = torrent_composer.compose()
    with open(output_file, 'wb') as f:
        f.write(composed_torrent)


if __name__ == '__main__':
    main()
