# PyPNG setup.py
# This is the setup.py script used by distutils.

# You can install the png module into your Python distribution with:
# python setup.py install
# You can also do other standard distutil type things, but you can refer
# to the distutil documentation for that.

# This script is also imported as a module by the Sphinx conf.py script
# in the man directory, so that this file forms a single source for
# metadata.

# http://docs.python.org/release/2.4.4/lib/module-sys.html
import sys

def get_version():
    from os.path import dirname, join
    for line in open(join(dirname(__file__), "code", "png.py")):
        if '__version__' in line:
            version = line.split('"')[1]
            break
    return version

conf = dict(
    name='pypng',
    version=get_version(),
    description='Pure Python PNG image encoder/decoder',
    long_description="""
PyPNG allows PNG image files to be read and written using pure Python.

It's available from github.com
https://github.com/drj11/pypng

Documentation is kindly hosted by PyPI
http://pythonhosted.org/pypng/
(and also available in the download tarball).
""",
    author='David Jones',
    author_email='drj@pobox.com',
    url='https://github.com/drj11/pypng',
    package_dir={'':'code'},
    py_modules=['png', 'test_png', 'pngsuite'],
    classifiers=[
      'Topic :: Multimedia :: Graphics',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.6',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.2',
      'Programming Language :: Python :: 3.3',
      'Programming Language :: Python :: 3.4',
      'License :: OSI Approved :: MIT License',
      'Operating System :: OS Independent',
      ],
    )
conf['download_url'] = \
  'https://github.com/drj11/pypng/archive/%(name)s-%(version)s.tar.gz' % conf

if __name__ == '__main__':
    try:
        # http://peak.telecommunity.com/DevCenter/setuptools#basic-use
        from setuptools import setup
        # distribute is probably installed, so use_2to3 should work
        conf['test_suite'] = "test_png"
    except ImportError:
        # http://docs.python.org/release/2.4.4/dist/setup-script.html
        from distutils.core import setup
    setup(**conf)
