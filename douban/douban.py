#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import json
from calibre.ebooks.metadata.sources.base import Source, Option
from calibre.ebooks.metadata.book.base import Metadata


class Douban(Source):
    name = 'Douban'
    description = 'Download metadata from douban.com'
    action_type = 'current'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Kevin Liao'
    version = (1, 0, 0)
    minimum_calibre_version = (2, 80, 0)

    capabilities = frozenset(['identify'])
    touched_fields = frozenset(
        ['title', 'authors', 'publisher', 'pubdate', 'comments', 'tags',
            'identifier:isbn', 'identifier:douban', 'rating', 'series']
    )

    options = (
        Option('apikey', 'string', '', _('douban api v2 apikey'),
               _('douban api v2 apikey')),
    )

    def to_metadata(self, book):
        from calibre.utils.date import parse_date
        mi = Metadata(book.get('title'), book.get('author'))
        subtitle = book.get('subtitle')
        if subtitle is not None and subtitle != '':
            mi.title += ': ' + subtitle
        mi.publisher = book.get('publisher')
        mi.pubdate = parse_date(book.get('pubdate'))
        mi.comments = book.get('summary')
        mi.tags = [x['name'] for x in book.get('tags', [])]
        mi.identifiers = {'douban': book.get('id')}
        mi.rating = float(book.get('rating', {}).get('average')) / 2
        mi.series = book.get('series', {}).get('title')
        mi.isbn = book.get('isbn13')
        return mi

    def identify(self, log, result_queue, abort, title=None,
                 authors=None, identifiers={}, timeout=30):
        ISBN_URL = 'https://api.douban.com/v2/book/isbn/{}?apikey={}'
        SEARCH_URL = 'https://api.douban.com/v2/book/search?q={}&count=10&apikey={}'
        SUBJECT_URL = 'https://api.douban.com/v2/book/{}?apikey={}'
        isbn = identifiers.get('isbn', None)

        if self.prefs['apikey'] == '':
            return

        if isbn is not None:
            url = ISBN_URL.format(isbn, self.prefs['apikey'])
            raw = self.browser.open_novisit(url, timeout=timeout).read()
            book = json.loads(raw)
            result_queue.put(self.to_metadata(book))
            return

        subject = identifiers.get('douban', None)
        if subject is not None:
            url = SUBJECT_URL.format(subject, self.prefs['apikey'])
            raw = self.browser.open_novisit(url, timeout=timeout).read()
            book = json.loads(raw)
            result_queue.put(self.to_metadata(book))
            return

        query_string = ''
        if title is not None:
            query_string += title + ' '
        if authors is not None:
            query_string += ' '.join(authors)
        if query_string != '':
            url = SEARCH_URL.format(query_string, self.prefs['apikey'])
            raw = self.browser.open_novisit(url, timeout=timeout).read()
            books = json.loads(raw)
            for book in books.get('books', []):
                result_queue.put(self.to_metadata(book))


if __name__ == '__main__':
    from calibre.ebooks.metadata.sources.test import (test_identify_plugin,
                                                      title_test, authors_test)
    test_identify_plugin(
            Douban.name,
            [
                (
                    {'identifiers': {'isbn': '9787115308108'},
                     'title': '具体数学'},
                    [title_test('具体数学', exact=False)]
                ),
            ])
