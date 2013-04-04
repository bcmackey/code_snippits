#!/usr/bin/env python

# Tester program to read and write JSON files with datetime support

import timeit
import json
import datetime
from bson import json_util
import re

example_doc = {'author': 'Ben Mackey',
               'version': 1,
               'last_update': datetime.datetime.now(),
               'list': [1, 2, 'string', 4],
               'embed': {'hello': 'world'}}

example_json = '''{"embed": {"hello": "world"}, "version": 1, "list": [1, 2, "string", 4], "last_update": "2013-04-04T14:09:51.648658", "author": "Ben Mackey"}'''


#######################################
## Encoding options
#######################################
def simple_date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


lambda_date_handler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None


class DateTimeJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return super(DateTimeJSONEncoder, self).default(obj)


#######################################
## Decoding options
#######################################
class DateTimeJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.datetime_decoder, *args, **kargs)

    def datetime_decoder(self, d):
        for (k, v) in d.items():
            try:
                if isinstance(v, unicode):
                    d[k] = datetime.datetime.strptime(
                        v, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                continue
        return d


class RegexDateTimeJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kargs):
        # Regex stolen from feed.date.rfc339 (http://home.blarg.net/~steveha/pyfeed.html)
        self.rfc339_regex = re.compile(r"""
(\d\d\d\d)\D+(\d\d)\D+(\d\d)  # year month day, separated by non-digit
\D+  # non-digit
(\d\d?)\D+(\d\d)\D+(\d\d)  # hour minute sec, separated by non-digit
([.,]\d+)?  # optional fractional seconds (American decimal or Euro ",")
\s*  # optional whitespace
(\w+|[-+]\d\d?\D*\d\d)?  # time offset: letter(s), or +/- hours:minutes
""", re.X)
        json.JSONDecoder.__init__(
            self, object_hook=self.datetime_decoder, *args, **kargs)

    def datetime_decoder(self, d):
        for (k, v) in d.items():
            try:
                if isinstance(v, unicode):
                    if self.rfc339_regex.match(v):
                        d[k] = datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                continue
        return d


#######################################
## Testing Functions
#######################################
def test_encode_simple():
    json.dumps(example_doc, default=simple_date_handler)


def test_encode_lambda():
    json.dumps(example_doc, default=lambda_date_handler)


def test_encode_jsonEncoder_class():
    json.dumps(example_doc, cls=DateTimeJSONEncoder)


def test_decode_jsonDecoder_class():
    json.loads(example_json, cls=DateTimeJSONDecoder)


def test_decode_regexJsonDecoder_class():
    json.loads(example_json, cls=RegexDateTimeJSONDecoder)


def test_encode_bson():
    json_util.dumps(example_doc)


def test_decode_bson():
    json_util.loads(example_json)

n = 10000
print "Testing each function with %d iterations" % n
funcs = dir()
for f in funcs:
    if f[:4] == 'test':
        a = timeit.timeit("%s()" % f, "from __main__ import %s" % (f), number=n)
        print "%0.6fs for %s" % (a, f)
