# SchemeDoc - An API and browser for Scheme documentation

**NOTE: The project is in very early experimentation/planning stage**

## The API

This is a REST API to access documentation pertaining to the Scheme
programming language.

The aspiration is to cover:

* Standards: R5RS, R6RS, R7RS
* SRFIs: all symbols defined in them, general information
* Implementations: SRFI support, bundled libraries, general information
* Community libraries (if this can be done with reasonable effort)
* Anything else people are motivated to add

Right now it provides just a little SRFI and implementation data.

The API is meant to be automatically up-to-date, versioned, easy to
parse and highly cross-referenced. These are still work in progress.

## The scraper

The API information is agglomerated by scraping files found around the
web. The process is error-prone and very incomplete. It could be
vastly improved by light standardization.

## Clients

The repo includes a simple web front end as a demo client. However,
the main point is to build a stable API. People could then build all
kinds of clients for various purposes.

## Hosting

The API currently runs on a free Heroku dyno. It doesn't require a
database.

## Implementation languages

The scraper and server are currently written in Python and the client
in Elm because that's what I had at hand. The server could easily be
written in Scheme if someone figures out painless deployment from Git
to a web host. The demo front end could be done using a Scheme->JS
compiler but it might be best to wait for a Scheme-native library in
the spirit of Elm or React. It's probably not worth rewriting the
scraper since it's just a pile of hacks. If scraping can be done in a
clean standardized manner across the Scheme community at some point,
then a clean Scheme implementation would make sense.

The API currently emits JSON. It would be easy to add equivalent
endpoints producing S-expressions. In fact, this would be one of the
first tasks to attempt.
