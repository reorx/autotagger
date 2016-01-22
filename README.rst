Autotagger
==========

Tag `.mp3` and `.m4a` audio files from iTunes data automatically.

There are various standards in audio file tagging, and the fields they contain
are huge mess, but since most of them are not being used by us normal people,
to make things simpler, I chose 8 essential and common fields pragmatically:

- Title
- Album
- Artist
- Album Artist
- Genre
- Release Date
- Track Number
- Disc Number

By default, autotagger will only work with these 8 fields, anything not included will be
ignored.

To make autotagger working properly, you should first find the iTunes url
for your album, autotagger take advantage of iTunes's awesome lookup API
and grab tagging data from it. For further usage and help information,
read the instructions below.

Install
-------

::

    pip install autotagger


Usage
-----

`autotagger --help` to see detailed information about command line options.

Input/Paste songs manually
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    autotagger -i 251480659

You can copy file paths by right click on songs in finder and choose ``Copy Path``

.. image:: images/r-origin-copy-path.png

::

    autotagger -u https://itunes.apple.com/us/album/schole-compilation-vol.-1/id251480659

You can use url instead of album id either


Pass songs from pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

::

    find album -type f -name '*.mp3' | autotagger -i 251480659 -p

Add ``-p`` option to enable this feature.


Clear other tags
~~~~~~~~~~~~~~~~

::

    autotagger -i 251480659 -c

Add ``-c`` to clear other tags.


Download artwork
~~~~~~~~~~~~~~~~

::

    autotagger -i 251480659 -a

Add ``-a`` option to download artwork, note this option will make the command stop tagging songs


Screenshots
-----------

``autotagger -i 251480659``

.. image:: images/r-origin-simple.png

``find album -type f -name '*.mp3' | autotagger -i 251480659 -p``

.. image:: images/r-origin-pipeline.png
