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

Install
-------

::

    pip install autotagger


Usage
-----

Run ``autotagger --help`` to see detailed information about command line options.

Input/Paste songs manually
~~~~~~~~~~~~~~~~~~~~~~~~~~

To make autotagger working properly, you should first find the iTunes url
for your album, autotagger take advantage of iTunes's awesome lookup API
and grab tagging data from it. use ``-u`` to indicate the itunes album url:

::

    autotagger -u https://itunes.apple.com/us/album/schole-compilation-vol.-1/id251480659

After running this command, autotagger will ask you to enter the file paths,
you can copy them by right click on songs in finder and choose ``Copy Path``

.. image:: images/r-origin-copy-path.png

Then paste them in the terminal, and hit enter to continue.

You can use url instead of album id to make the command clearer:

::

    autotagger -i 251480659


Pass songs from pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

If you can get the song names from other command's output, you can use
pipeline mode to feed the input, add ``-p`` option to enable this feature:

::

    find album -type f -name '*.mp3' | autotagger -i 251480659 -p


Clear other tags
~~~~~~~~~~~~~~~~

If you want the songs to be tagged just the 8 fields other than anything else,
you can add ``-c`` to achieve that. By adding this option, only the 8 fields
will be contained in the songs, any other fields will be removed.

::

    autotagger -i 251480659 -c


Download artwork
~~~~~~~~~~~~~~~~

Add ``-a`` option to download artwork, note this option will make the command stop tagging songs.

::

    autotagger -i 251480659 -a


Screenshots
-----------

``autotagger -i 251480659``

.. image:: images/r-origin-simple.png

``find album -type f -name '*.mp3' | autotagger -i 251480659 -p``

.. image:: images/r-origin-pipeline.png
