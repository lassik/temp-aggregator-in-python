#!/bin/sh
set -eu
grep -ohE '(class|id)=[^ >]+' .cache/srfi-*.html | tr -d '"'"'" | sort | uniq
