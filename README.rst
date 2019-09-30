Electron Cash - Lightweight Bitcoin Cash client
=====================================

::

  Licence: MIT Licence
  Author: Jonald Fyookball
  Language: Python
  Homepage: https://electroncash.org/


.. image:: https://d322cqt584bo4o.cloudfront.net/electron-cash/localized.svg
    :target: https://crowdin.com/project/electron-cash
    :alt: Help translate Electron Cash online



For info about project:

https://github.com/orgs/SLPVH/teams/george-bush-faked-the-moonlandings

Getting started
===============

Electron Cash is a pure python application forked from Electrum. If you want to use the
Qt interface, install the Qt dependencies::

    sudo apt-get install python3-pyqt5 python3-pyqt5.qtsvg

If you downloaded the official package (tar.gz), you can run
Electron Cash from its root directory (called Electrum), without installing it on your
system; all the python dependencies are included in the 'packages'
directory. To run Electron Cash from its root directory, just do::

    ./electron-cash

You can also install Electron Cash on your system, by running this command::

    sudo apt-get install python3-setuptools
    python3 setup.py install

This will download and install the Python dependencies used by
Electron Cash, instead of using the 'packages' directory.

If you cloned the git repository, you need to compile extra files
before you can run Electron Cash. Read the next section, "Development
Version".



Development version
===================

Check out the code from Github::

    git clone https://github.com/Electron-Cash/Electron-Cash
    cd Electron-Cash

Run install (this should install dependencies)::

    python3 setup.py install

or for Debian based systems ( tested on Debian v9 Stretch )::

    sudo apt update
    sudo apt install python3-dnspython python3-pyaes libsecp256k1-0 python3-protobuf python3-jsonrpclib-pelix python3-ecdsa python3-qrcode python3-pyqt5 python3-socks

Then

Compile the protobuf description file::

    sudo apt-get install protobuf-compiler
    protoc --proto_path=lib/ --python_out=lib/ lib/paymentrequest.proto

Create translations (optional)::

    sudo apt-get install python-requests gettext
    ./contrib/make_locale

For plugin development, see the `plugin documentation <plugins/README.rst>`_.

Running unit tests::

    pip install tox
    tox

Tox will take care of building a faux installation environment, and ensure that
the mapped import paths work correctly.

Creating Binaries
=================

Linux AppImage & Source Tarball
--------------

See `contrib/build-linux/README.md <contrib/build-linux/README.md>`_.

Mac OS X / macOS
--------

See `contrib/osx/ <contrib/osx/>`_.

Windows
-------

See `contrib/build-wine/ <contrib/build-wine/>`_.

Android
-------

See `gui/kivy/Readme.txt <gui/kivy/Readme.txt>`_ file.

iOS
-------

See `ios/ <ios/>`_.
