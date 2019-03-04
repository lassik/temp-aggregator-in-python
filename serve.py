#! /usr/bin/env python3

import json
import os

from os.path import join

from bottle import abort, route, run, static_file, template


ROOT = os.path.dirname(__file__)
STATICDIR = join(ROOT, "static")
SRFI = json.load(open(join(ROOT, "srfi.json")))
global_symbols = {}


def update_symbols_with_srfi(symbols):
    for srfi in SRFI.values():
        srfi_number = srfi["number"]
        for symbol in srfi["symbols"]:
            symbols[symbol] = symbols.get(symbol, [])
            symbols[symbol].append(
                {
                    "defined_in": {"type": "srfi", "number": srfi_number},
                    "type": "procedure",
                }
            )


@route("/")
def serve_main():
    return static_file("index.html", root=join(ROOT))


@route("/static/<filename>")
def serve_static(filename):
    return static_file(filename, root=STATICDIR)


@route("/unstable/srfi")
def serve_srfi():
    return {"data": list(sorted(SRFI.values(), key=lambda srfi: srfi["number"]))}


@route("/unstable/srfi/<number>")
def serve_srfi_number(number):
    try:
        return SRFI[number]
    except KeyError:
        abort(404, "SRFI not found")


@route("/unstable/symbol")
def serve_symbol():
    return global_symbols


@route("/unstable/symbol/<name>")
def serve_symbol(name):
    try:
        return {"name": name, "definitions": global_symbols[name]}
    except KeyError:
        abort(404, "Symbol not found")


update_symbols_with_srfi(global_symbols)
run(port=int(os.environ["PORT"]))
