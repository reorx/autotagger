#!/usr/bin/env python
# coding: utf-8

from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4


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

# Based on exports from iTunes
# general key -> mutagen id3 key
MUTAGEN_ID3_KEY_MAP = {
    'title': 'title',
    'album': 'album',
    'artist': 'artist',
    'album_artist': 'performer',
    'genre': 'genre',
    'release_date': 'date',
    'track_number': 'tracknumber',
    'disc_number': 'discnumber',
}

# Based on exports from iTunes
# general key -> mutagen id3 key
MUTAGEN_M4A_KEY_MAP = {
    'title': 'title',
    'album': 'album',
    'artist': 'artist',
    'album_artist': 'albumartist',
    'genre': 'genre',
    'release_date': 'date',
    'track_number': 'tracknumber',
    'disc_number': 'discnumber',
}


def fetch_album_songs(album_id):
    pass


def format_itunes_data(origin):
    pass


def tag_song(filename, tags):
    pass


def main():
    pass


if __name__ == '__main__':
    main()
