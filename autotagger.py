#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

import re
import os
import sys
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

        logger.debug('mutagen obj: %s', self.mutagen_obj)

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

        if clear_others:
            # Delete old
            self.mutagen_obj.delete()
            # Create new
            self.mutagen_obj = self.mutagen_factory(self.filepath)

        for k, v in tags.iteritems():
            mutagen_key = self.key_map[k]
            self.mutagen_obj[mutagen_key] = str(v)

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
    return s


ITUNES_API_ALBUM_URL = 'https://itunes.apple.com/lookup?id={}&entity=song'


def fetch_album_songs(album_id):
    url = ITUNES_API_ALBUM_URL.format(album_id)
    resp = requests.get(url)
    data = resp.json()
    return data['results'][1:]


# general key -> itunes api key
ITUNES_API_KEY_MAP = {
    'title': 'trackName',
    'album': 'collectionName',
    'artist': 'artistName',
    'album_artist': 'collectionArtistName',
    'genre': 'primaryGenreName',
    'release_date': 'releaseDate',
    'track_number': 'trackNumber',
    'disc_number': 'discNumber',
}


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
    # Show preview
    args_tuples = []
    for id, song in songs_col.iteritems():
        args_tuples.append((song, songs_data_col.get(id)))

    preview = u'\n'.join(
        u'{}  →  {}'.format(
            _cell(i.filename),
            _cell(_get_title(j))
        ) for i, j in args_tuples)
    print('Preview:')
    print(preview)

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
        align_pos = - limit + 2
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
        return rv.group()
    return None


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

    parser.add_argument('-c', '--clear-others', action='store_true',
                        help='Clear other tags')

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

    album_id = args.album_id
    if not album_id:
        album_id = get_id_from_url(args.url)

    if not album_id:
        raise ValueError('Could not get album id from arguments')

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
                    break

    songs = filter(None, songs)
    logger.debug('input songs:%s', songs)

    tag_songs(songs, album_id, clear_others=args.clear_others)


if __name__ == '__main__':
    main()
