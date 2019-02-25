#! /usr/bin/env python3


import json
import mimetypes
import tarfile
import os
import re
import shutil
import sys
import urllib.request

from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer

from bs4 import BeautifulSoup  # pip3 install beautifulsoup4


CACHEDIR = os.path.join(os.path.dirname(__file__), ".cache")
STATICDIR = os.path.join(os.path.dirname(__file__), "static")


def url_cachefile(cachefile_basename, url):
    cachefile = os.path.join(CACHEDIR, cachefile_basename)
    os.makedirs(os.path.dirname(cachefile), exist_ok=True)
    if not os.path.exists(cachefile):
        print("Downloading", url, file=sys.stderr)
        with urllib.request.urlopen(url) as response:
            with open(cachefile, "wb") as output:
                shutil.copyfileobj(response, output)
    return cachefile


def url_text(cachefile_basename, url):
    cachefile = url_cachefile(cachefile_basename, url)
    with open(cachefile, "r", encoding="utf-8") as input:
        return input.read()


def dict_with_sorted_values(items):
    dict_ = {}
    for key, values in items:
        dict_[key] = list(sorted(values))
    return dict_


def is_non_placeholder_symbol(s):
    return bool(re.match(r"^[a-z@*+/-][a-zA-Z0-9@?!<>*/+-]*", s))


# ================================================================================


def r4rs_tarfile():
    return tarfile.open(
        url_cachefile(
            "r4rs.tar.gz",
            "https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r4rs.tar.gz",
        )
    )


def r5rs_tarfile():
    return tarfile.open(
        url_cachefile(
            "r5rs.tar.gz",
            "https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r5rs.tar.gz",
        )
    )


def r6rs_tarfile():
    return tarfile.open(
        url_cachefile("r6rs.tar.gz", "http://www.r6rs.org/final/r6rs.tar.gz")
    )


def r4rs_symbols():
    symbols = set()
    tarfile = r4rs_tarfile()
    for info in tarfile:
        if info.name.endswith(".tex"):
            tex_file = tarfile.extractfile(info).read().decode("US-ASCII")
            for symbol in re.findall(r"{\\cf (.*?)}", tex_file):
                symbols.add(symbol)
    return symbols


# ================================================================================


def all_srfi_numbers():
    return [1 + i for i in range(165)]


def srfi_cachefile(srfi_number):
    return "srfi-{}.html".format(srfi_number)


def srfi_official_html_url(srfi_number):
    return "https://srfi.schemers.org/srfi-{}/srfi-{}.html".format(
        srfi_number, srfi_number
    )


def srfi_github_html_url(srfi_number):
    return (
        "https://raw.githubusercontent.com/scheme-requests-for-implementation"
        "/srfi-{}/master/srfi-{}.html".format(srfi_number, srfi_number)
    )


def srfi_raw_html(srfi_number):
    return url_text(srfi_cachefile(srfi_number), srfi_github_html_url(srfi_number))


def srfi_html_soup(srfi_number):
    return BeautifulSoup(srfi_raw_html(srfi_number), "html.parser")


def srfi_title(srfi_number):
    title = srfi_html_soup(srfi_number).find("title").text.strip()
    match = re.match(r"SRFI \d+: (.*)", title)
    return match.group(1) if match else title


def srfi_list_heads_from_code_tags(srfi_number):
    return [
        match.group(1)
        for match in [
            re.match(r"^\(([^\s()]+)", tag.text.strip())
            for tag in srfi_html_soup(srfi_number).find_all("code")
        ]
        if match
    ]


def srfi_defined_symbols(srfi_number):
    return list(
        sorted(
            filter(
                is_non_placeholder_symbol,
                set(srfi_list_heads_from_code_tags(srfi_number)),
            )
        )
    )


def all_srfi_defined_symbols():
    return [
        (srfi_number, symbol)
        for srfi_number in all_srfi_numbers()
        for symbol in srfi_defined_symbols(srfi_number)
    ]


def srfi_to_symbol_map():
    sets = defaultdict(set)
    for srfi_number, symbol in all_srfi_defined_symbols():
        sets[srfi_number].add(symbol)
    return dict_with_sorted_values(sets.items())


def symbol_to_srfi_map():
    sets = defaultdict(set)
    for srfi_number, symbol in all_srfi_defined_symbols():
        sets[symbol].add(srfi_number)
    return dict_with_sorted_values(sets.items())


def srfi_map():
    return {
        srfi_number: {
            "number": srfi_number,
            "title": srfi_title(srfi_number),
            "official_html_url": srfi_official_html_url(srfi_number),
            "github_html_url": srfi_github_html_url(srfi_number),
        }
        for srfi_number in all_srfi_numbers()
    }


# ================================================================================


def all_static_files():
    ans = {}
    for name in os.listdir(STATICDIR):
        if not name.startswith("."):
            full = os.path.join(STATICDIR, name)
            if os.path.isfile(full):
                ans["/static/" + name] = open(full, "rb").read()
    for name in sorted(ans.keys()):
        print("Static", name, file=sys.stderr)
    return ans


class WebApi(BaseHTTPRequestHandler):
    def respond_with_error(self, status_code, status_text):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=US-ASCII")
        self.end_headers()
        self.wfile.write(status_text.encode("US-ASCII"))

    def respond_with_json(self, obj):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=US-ASCII")
        self.end_headers()
        self.wfile.write(
            json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=4).encode(
                "US-ASCII"
            )
        )

    def respond_with_static(self, path, static):
        mimetype, _ = mimetypes.guess_type(path)
        self.send_response(200)
        if mimetype:
            self.send_header("Content-Type", mimetype)
        self.end_headers()
        self.wfile.write(static)

    def do_GET(self):
        routes = {
            "/srfi-map.json": lambda: self.respond_with_json(srfi_map()),
            "/symbol-to-srfi-map.json": lambda: self.respond_with_json(
                symbol_to_srfi_map()
            ),
            "/srfi-to-symbol-map.json": lambda: self.respond_with_json(
                srfi_to_symbol_map()
            ),
        }
        route = routes.get(self.path, None)
        if route:
            route()
            return
        static = all_static_files().get(self.path, None)
        if static:
            self.respond_with_static(self.path, static)
            return
        self.respond_with_error(404, "Not Found")


def serve_locally(port=8080):
    HTTPServer(("localhost", port), WebApi).serve_forever()
