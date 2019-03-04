#! /usr/bin/env python3


import json
import mimetypes
import os
import re
import shutil
import string
import sys
import tarfile
import urllib.parse
import urllib.request

from collections import defaultdict, namedtuple
from http.server import BaseHTTPRequestHandler, HTTPServer

from bs4 import BeautifulSoup  # pip3 install beautifulsoup4

Symbol = namedtuple("Symbol", "name")

CACHEDIR = os.path.join(os.path.dirname(__file__), ".cache")


def url_cachefile(url, basename=None):
    basename = basename or os.path.basename(urllib.parse.urlparse(url).path)
    assert len(basename)
    cachefile = os.path.join(CACHEDIR, basename)
    os.makedirs(os.path.dirname(cachefile), exist_ok=True)
    if not os.path.exists(cachefile):
        print("Downloading", url, file=sys.stderr)
        with urllib.request.urlopen(url) as response:
            with open(cachefile, "wb") as output:
                shutil.copyfileobj(response, output)
    return cachefile


def url_text(url, basename=None):
    cachefile = url_cachefile(url, basename)
    with open(cachefile, "r", encoding="utf-8") as input:
        return input.read()


def replace_file_contents(filename, new_bytes):
    newfilename = filename + ".new"
    with open(newfilename, "wb") as output:
        output.write(new_bytes)
    os.rename(newfilename, filename)


def to_lisp(obj, toplevel=False):
    if isinstance(obj, list):
        return (
            "("
            + ("\n" if toplevel else " ").join(map(to_lisp, obj))
            + ")"
            + ("\n" if toplevel else "")
        )
    if isinstance(obj, Symbol):
        return obj.name
    if isinstance(obj, str):
        safe = string.ascii_letters + string.digits + " !#$%&'()*+,-./:;<=>?@[\]^_`{|}~"
        for ch in obj:
            if ch not in safe:
                raise ValueError(
                    "Char {} in string {} unsafe for Lisp".format(repr(ch), repr(obj))
                )
        return '"' + obj + '"'
    if isinstance(obj, int):
        return str(obj)
    assert False


def emit_lisp_file(filename, obj):
    lisp = to_lisp(obj, True)
    replace_file_contents(filename, lisp.encode("US-ASCII"))


def emit_json_file(filename, obj):
    json_ = json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=4)
    replace_file_contents(filename, json_.encode("US-ASCII"))


def dict_with_sorted_values(items):
    dict_ = {}
    for key, values in items:
        dict_[key] = list(sorted(values))
    return dict_


def numbers_matching_regexp(regexp, items):
    matches = filter(None, (re.match(regexp, item) for item in items))
    return list(sorted(set(int(match.group(1)) for match in matches)))


def is_non_placeholder_symbol(s):
    return bool(re.match(r"^[a-z@*+/-][a-zA-Z0-9@?!<>*/+-]*", s))


# ================================================================================


def r4rs_tarfile():
    return tarfile.open(
        url_cachefile(
            "https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r4rs.tar.gz"
        )
    )


def r5rs_tarfile():
    return tarfile.open(
        url_cachefile(
            "https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r5rs.tar.gz"
        )
    )


def r6rs_tarfile():
    return tarfile.open(url_cachefile("http://www.r6rs.org/final/r6rs.tar.gz"))


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


MIN_SRFI_NUMBER = 0
MAX_SRFI_NUMBER = 165


def all_srfi_numbers():
    return [i for i in range(MIN_SRFI_NUMBER, MAX_SRFI_NUMBER + 1)]


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
    return url_text(srfi_github_html_url(srfi_number), srfi_cachefile(srfi_number))


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


def emit_srfi():
    the_map = srfi_map()
    for srfi_number, info in the_map.items():
        the_map[srfi_number]["symbols"] = []
    for srfi_number, symbols in srfi_to_symbol_map().items():
        the_map[srfi_number]["symbols"] = symbols
    emit_json_file("srfi.json", the_map)
    emit_lisp_file(
        "srfi.lisp",
        [
            [
                srfi_number,
                [Symbol("title"), info["title"]],
                [Symbol("symbols")] + info["symbols"],
            ]
            for srfi_number, info in the_map.items()
        ],
    )


# ================================================================================


def impl_chibi_tarfile():
    return tarfile.open(
        url_cachefile("http://synthcode.com/scheme/chibi/chibi-scheme-0.8.0.tgz")
    )


def impl_chibi_srfi_list():
    return numbers_matching_regexp(
        r"chibi-scheme-.*?/lib/srfi/(\d+).sld",
        (entry.name for entry in impl_chibi_tarfile()),
    )


def impl_chibi():
    return {
        "id": "chibi",
        "title": "Chibi-Scheme",
        "homepage_url": "http://synthcode.com/wiki/chibi-scheme",
        "srfi_implemented": impl_chibi_srfi_list(),
    }


def impl_guile_tarfile():
    return tarfile.open(
        url_cachefile("https://ftp.gnu.org/gnu/guile/guile-2.2.4.tar.gz")
    )


def impl_guile_srfi_list():
    # Some SRFI implementations are single files, others are directories.
    return numbers_matching_regexp(
        r"guile-.*?/module/srfi/srfi-(\d+)",
        (entry.name for entry in impl_guile_tarfile()),
    )


def impl_guile():
    return {
        "id": "guile",
        "title": "Guile",
        "homepage_url": "https://www.gnu.org/software/guile/",
        "srfi_implemented": impl_guile_srfi_list(),
    }


def emit_implementation():
    emit_json_file("implementation.json", [impl_chibi(), impl_guile()])
