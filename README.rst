Autotagger
==========

Tag `.mp3` and `.m4a` audio files from iTunes data automatically.


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
