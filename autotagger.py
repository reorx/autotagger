#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

import re
import os
import sys
import shutil
import logging
import datetime
import argparse
import requests
import unicodedata
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.id3 import ID3
import mutagen.id3._util


extra_id3_tags = [
    ('comments', 'COMM')
]


for k, v in extra_id3_tags:
    EasyID3.RegisterTextKey(k, v)


logger = logging.getLogger()


def load_mp3(filename):
    try:
        return EasyID3(filename)
    except mutagen.id3._util.ID3NoHeaderError:
        # Fix mp3 file no tag loading error, m4a has no this problem
        id3 = ID3()
        id3.save(filename)
        return EasyID3(filename)


def load_m4a(filename):
    return EasyMP4(filename)


SUPPORT_EXTS = {
    'mp3': load_mp3,
    'm4a': load_m4a,
}


# Keys used by autotagging as unified interface
GENERAL_KEYS = [
    'title',
    'album',
    'artist',
    'album_artist',
    'genre',
    'release_date',
    'track_number',
    'disc_number',
]


# general key -> itunes api key
ITUNES_API_KEY_MAP = {
    'title': 'trackName',
    'album': 'collectionName',
    'artist': 'artistName',
    'album_artist': 'collectionArtistName',  # may not exists
    'genre': 'primaryGenreName',
    'release_date': 'releaseDate',
    'track_number': 'trackNumber',
    'disc_number': 'discNumber',
}


AVAILABLE_LANGUAGES = ['en_us', 'ja_jp']
DEFAULT_LANGUAGE = 'en_us'
DEFAULT_COUNTRY = 'US'

GLOBAL_CONTEXT = {
    'language': DEFAULT_LANGUAGE,
    'country': DEFAULT_COUNTRY,
}


class Song(object):
    # Based on exports from iTunes: general key -> mutagen id3 key
    MUTAGEN_KEY_MAPS = {
        'mp3': {
            'title': 'title',
            'album': 'album',
            'artist': 'artist',
            'album_artist': 'performer',
            'genre': 'genre',
            'release_date': 'date',
            'track_number': 'tracknumber',
            'disc_number': 'discnumber',
        },
        'm4a': {
            'title': 'title',
            'album': 'album',
            'artist': 'artist',
            'album_artist': 'albumartist',
            'genre': 'genre',
            'release_date': 'date',
            'track_number': 'tracknumber',
            'disc_number': 'discnumber',
        }
    }

    def __init__(self, filepath):
        self.filepath = filepath
        filename = to_unicode(os.path.basename(filepath))
        self.filename = filename
        ext = get_and_check_ext(filename)
        self.ext = ext
        self.mutagen_factory = SUPPORT_EXTS[ext]
        self.mutagen_obj = self.mutagen_factory(filepath)
        self.key_map = Song.MUTAGEN_KEY_MAPS[ext]
        self.reversed_key_map = {v: k for k, v in self.key_map.iteritems()}

        #logger.debug('mutagen obj: %s', self.mutagen_obj)

        track_number = self.get('track_number')
        disc_number = self.get('disc_number')

        if not track_number:
            raise ValueError('Require track number exist in song %s' % filename)

        if not disc_number:
            disc_number = ''

        self.id = generate_id(track_number, disc_number)

    def get(self, key):
        mutagen_key = self.key_map[key]
        v = self.mutagen_obj.get(mutagen_key)
        if v:
            return v[0]
        return None

    def update_tags(self, tags, clear_others=False):
        logger.info(u'Tag song: %s', self.filename)
        logger.debug('with tags: %s' % tags)

        if clear_others:
            # Delete old
            self.mutagen_obj.delete()
            # Create new
            self.mutagen_obj = self.mutagen_factory(self.filepath)

        for k, v in tags.iteritems():
            mutagen_key = self.key_map[k]
            if v is None:
                if mutagen_key in self.mutagen_obj:
                    del self.mutagen_obj[mutagen_key]
                else:
                    # Leave this key unchanged
                    pass
            else:
                self.mutagen_obj[mutagen_key] = to_unicode(v)

        self.mutagen_obj.save()

    def __repr__(self):
        return str(self)

    def __unicode__(self):
        return u'<Song: {}>'.format(self.filename)

    def __str__(self):
        return unicode(self).encode('utf8')


def slash_first_item(s):
    if isinstance(s, basestring):
        sp = s.split('/')
        if len(sp) > 1:
            return sp[0]
    return s


def generate_id(track_number, disc_number):
    if not disc_number:
        disc_number = '1'

    id = '{}-{}'.format(
        slash_first_item(track_number),
        slash_first_item(disc_number)
    )
    return id


def to_unicode(s):
    if isinstance(s, str):
        return s.decode('utf8')
    else:
        return unicode(s)


def to_str(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    else:
        return str(s)


ITUNES_API_ALBUM_URL = 'https://itunes.apple.com/lookup?id={}&entity=song&limit=200&lang={}&country={}'


class ResultIsEmpty(Exception):
    pass


def fetch_album_songs(album_id, only_songs=True, context=GLOBAL_CONTEXT):
    url = ITUNES_API_ALBUM_URL.format(album_id, context['language'], context['country'])
    logger.info('Fetching itunes data: %s', url)
    resp = requests.get(url)
    data = resp.json()
    results = data['results']
    if not len(results):
        raise ResultIsEmpty('Response is: {}'.format(resp.content.strip()))
    if only_songs:
        return results[1:]
    else:
        return results


def format_song_data(origin):
    d = {k: origin.get(v) for k, v in ITUNES_API_KEY_MAP.iteritems()}

    d['track_number'] = '{}/{}'.format(d['track_number'], origin['trackCount'])

    d['disc_number'] = '{}/{}'.format(d['disc_number'], origin['discCount'])

    if d['release_date']:
        dt = datetime.datetime.strptime(d['release_date'], "%Y-%m-%dT%H:%M:%SZ")
        d['release_date'] = dt.year

    return d


def tag_songs(songs, album_id, clear_others=False, need_confirm=True):
    songs_col = {}

    for filename in songs:
        song = Song(filename)

        if song.id in songs_col:
            raise ValueError('Conflict track number: %s - %s' % (filename, song.id))
        songs_col[song.id] = song

    logger.debug('song_col: %s', songs_col)

    # Prepare data
    songs_data_col = {}
    songs_data = fetch_album_songs(album_id)
    logger.debug('origin song data [0]: %s', songs_data[0])
    for _song_data in songs_data:
        song_data = format_song_data(_song_data)
        _id = generate_id(song_data['track_number'], song_data['disc_number'])
        songs_data_col[_id] = song_data

    logger.debug('formatted song data [0]: %s', songs_data_col.values()[0])

    # Prepare arguments
    args_tuples = []
    preview_tuples = []
    unmatched_count = 0
    songs_data_col_stack = dict(songs_data_col)
    for id, song in songs_col.iteritems():
        song_data = songs_data_col_stack.pop(id, None)
        if song_data is None:
            # Unmatched song data
            preview_tuples.append(
                (song.filename, False, '<no data>', '?')
            )
            unmatched_count += 1
        else:
            args_tuples.append(
                (song, song_data)
            )
            preview_tuples.append(
                (song.filename, True, _get_title(song_data), _get_track_number(song_data))
            )

    # Unmatched song file
    preview_tuples.extend([
        ('<no song>', False, _get_title(i), _get_track_number(i))
        for i in songs_data_col_stack.itervalues()
    ])
    unmatched_count += len(songs_data_col_stack)
    preview = u'\n'.join(
        u'{}  {}  {}  {}'.format(
            _cell(i),
            u'→' if is_good else u'✗',
            _cell(j),
            k,
        ) for i, is_good, j, k in preview_tuples)

    # Show preview and stats
    print('\nPreview:')
    good_count = len(filter(lambda x: x[1], preview_tuples))
    stat_str = '{} input, {} could be processed, {} unmatched, {}'.format(
        len(songs_col), good_count, unmatched_count,
        'better to recheck :/' if unmatched_count else 'looks good :)')
    print(preview)
    print()
    print(stat_str)

    if need_confirm:
        # Fix stdin being redirected when using pipeline:
        # http://stackoverflow.com/a/7141375/596206
        sys.stdin = open('/dev/tty')
        iv = raw_input('Continue? y/N')
        if iv == 'N':
            return

    # Start converting
    for song, tags in args_tuples:
        song.update_tags(tags, clear_others=clear_others)


def _cell(s, limit=35):
    #print(repr(s))
    s = to_unicode(s)
    width = unicode_width(s)
    if width > limit:
        align_pos = - limit + 4
        s = s[align_pos:]
        return u'…' + u' ' * (limit - unicode_width(s)) + s
    else:
        return u' ' + u' ' * (limit - unicode_width(s)) + s


def unicode_width(string):
    def char_width(char):
        # ('F', 'W', 'A', 'H', 'N', 'Na')
        # Ref: http://www.unicode.org/reports/tr11/tr11-14.html
        w2 = ('F', 'W', 'A')
        w1 = ('H', 'Na')
        w = unicodedata.east_asian_width(char)
        if w in w2:
            return 2
        elif w in w1:
            return 1
        else:
            return 0
    length = sum([char_width(c) for c in string])
    return length


def _get_title(o):
    if o is None:
        return u''
    else:
        return o.get('title')


def _get_track_number(o):
    if o is None:
        return u'?'
    else:
        return o.get('track_number')


def get_and_check_ext(filename):
    sp = filename.split('.')
    if len(sp) < 2:
        raise ValueError('Invalid file name %s, ext required' % filename)
    ext = sp[-1]
    if ext not in SUPPORT_EXTS:
        raise ValueError('Ext %s not supported yet, currently support %s' % (ext, SUPPORT_EXTS))
    return ext


ID_REGEX = re.compile(r'id(\d+)\/?$')


def get_id_from_url(url):
    rv = ID_REGEX.search(url)
    if rv:
        return rv.groups()[0]
    return None


ALBUM_NAME_KEY = 'collectionName'


def download_artwork(album_id, artwork_size):
    data = fetch_album_songs(album_id, only_songs=False)
    album_data = data[0]
    size_repr = artwork_size + 'x' + artwork_size
    artwork_url = album_data['artworkUrl100'].replace('100x100', size_repr)
    logger.info('Download from url: %s', artwork_url)

    # get album name
    album_name = album_data[ALBUM_NAME_KEY]
    album_name = album_name.strip().replace(' ', '')

    filename = '{}-{}.jpg'.format(album_name, size_repr)

    resp = requests.get(artwork_url, stream=True)
    if resp.status_code < 300:
        with open(filename, 'wb') as f:
            logging.info('Write to file: %s', filename)
            shutil.copyfileobj(resp.raw, f)
    else:
        print('Download failed with status %s, %s', resp.status_code, resp.content)
        sys.exit(1)


def main():
    usage_example = """Examples:
  By ID:
    autotagger -i 251480659
  By URL:
    autotagger --url https://itunes.apple.com/us/album/schole-compilation-vol.-1/id251480659
  Pipe file names:
    find . -type f -name '*.mp3' -mtime -5m | autotagger -i 251480659 -p
"""

    parser = argparse.ArgumentParser(
        description='Automatically tag the given songs from an iTunes album id/url',
        epilog=usage_example,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    # options
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', '--album-id', type=str, metavar='ALBUMID',
                       help='iTunes album id')
    group.add_argument('-u', '--url', type=str, metavar='ALBUMURL',
                       help='iTunes album url')

    parser.add_argument('-p', '--pipeline', action='store_true',
                        help='Read songs from pipe line')

    parser.add_argument('-C', '--clear-others', action='store_true',
                        help='Clear other tags')

    parser.add_argument('-a', '--download-artwork', action='store_true',
                        help='Download artwork, do this only')

    parser.add_argument('--artwork-size', type=str, default='500',
                        help='Specify artwork size, default is 500, use with `-a` option')

    parser.add_argument('-l', '--language', type=str, metavar='LANGUAGE', default=DEFAULT_LANGUAGE,
                        help='The language you want to use for song name, available values: en_us, ja_jp')

    parser.add_argument('-c', '--country', type=str, metavar='COUNTRY', default=DEFAULT_COUNTRY,
                        help='Country code (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)')

    args = parser.parse_args()

    # Configure logging
    level_str = os.environ.get('LOGGING_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, level_str),
        format='[ %(levelname)7s %(module)s:%(lineno)d ] %(message)s',
        #format='[ %(levelname)7s ] %(name)s %(module)s:%(lineno)d %(message)s',
    )
    # Disable requests loggers' propagation
    logging.getLogger('requests').propagate = 0

    logger.debug('args: %s', args)

    # Check args
    album_id = args.album_id
    if not album_id:
        album_id = get_id_from_url(args.url)

    if not album_id:
        raise ValueError('Could not get album id from arguments')

    if args.language:
        if args.language not in AVAILABLE_LANGUAGES:
            raise ValueError('language could only be one of %s' % AVAILABLE_LANGUAGES)
        GLOBAL_CONTEXT['language'] = args.language

    if args.country:
        GLOBAL_CONTEXT['country'] = args.country

    if args.download_artwork:
        download_artwork(album_id, args.artwork_size)
        return

    if args.pipeline:
        user_input = sys.stdin.read()
        songs = user_input.split('\n')
    else:
        print('Paste song file names here:\n')
        songs = []
        while True:
            i = raw_input()
            if i:
                songs.append(i)
            else:
                c = raw_input('Stop adding songs and start tagging? (enter or y to confirm, N to continue adding.) ')
                if c == '' or c == 'y':
                    print()
                    break

    songs = filter(None, songs)
    logger.debug('input songs:%s', songs)

    tag_songs(songs, album_id, clear_others=args.clear_others)


if __name__ == '__main__':
    main()
