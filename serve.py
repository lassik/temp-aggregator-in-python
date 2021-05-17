#! /usr/bin/env python3

import json
import os

from os.path import join

from bottle import abort, route, run, static_file


ROOT = os.path.dirname(__file__)


class DB:
    def __init__(self, root):
        self.srfi = json.load(open(join(root, "srfi.json")))
        self.impl = json.load(open(join(root, "implementation.json")))
        self.symbols = {}
        self._update_symbols_with_srfi()
        self._update_srfi_with_implementations()

    def _update_symbols_with_srfi(self):
        for srfi in self.srfi.values():
            srfi_number = srfi["number"]
            for symbol in srfi["symbols"]:
                self.symbols[symbol] = self.symbols.get(symbol, [])
                self.symbols[symbol].append(
                    {
                        "defined_in": {"type": "srfi", "number": srfi_number},
                        "type": "procedure",
                    }
                )

    def _update_srfi_with_implementations(self):
        for srfi in self.srfi.values():
            srfi["implementations"] = []
        for impl in sorted(self.impl, key=lambda impl: impl["id"]):
            for srfi_number in impl["srfi_implemented"]:
                self.srfi[str(srfi_number)]["implementations"].append(impl["id"])

    def impl_by_id(self, impl_id):
        return next(impl for impl in self.impl if impl["id"] == impl_id)


db = DB(ROOT)


@route("/")
def serve_main():
    return static_file("index.html", root=join(ROOT))


@route("/elm.min.js")
def serve_main():
    return static_file("elm.min.js", root=join(ROOT))


@route("/unstable/srfi")
def serve_srfi():
    return {"data": list(sorted(db.srfi.values(), key=lambda srfi: srfi["number"]))}


@route("/unstable/srfi/<number>")
def serve_srfi_number(number):
    try:
        return db.srfi[number]
    except KeyError:
        abort(404, "SRFI not found")


@route("/unstable/symbol")
def serve_symbol():
    return db.symbols


@route("/unstable/symbol/<name>")
def serve_symbol_name(name):
    try:
        return {"name": name, "definitions": db.symbols[name]}
    except KeyError:
        abort(404, "Symbol not found")


@route("/unstable/implementation")
def serve_implementation():
    return {"data": db.impl}


@route("/unstable/implementation/<impl_id>")
def serve_implementation_id(impl_id):
    try:
        return db.impl_by_id(impl_id)
    except KeyError:
        abort(404, "Implementation not found")


run(host="0", port=int(os.environ["PORT"]))
