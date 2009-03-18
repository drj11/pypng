# $URL$
# $Rev$

# PyPNG setup.py
# This is the setup.py script used by disutils.

# You can install the png module into your Python distribution with:
# python setup.py install
# You can also do other standard disutil type things, but you can refer
# to the disutil documentation for that.

# This script is also imported as a module by the Sphinx conf.py script
# in the man directory, so that they can share metadata.

conf = dict(
    name='pypng',
    version='0.0.2',
    description='Pure Python PNG encoder/decoder',
    author='David Jones',
    author_email='drj@pobox.com',
    url='http://code.google.com/p/pypng/',
    package_dir={'':'code'},
    py_modules=['png'],
    )

if __name__ == '__main__':
    from distutils.core import setup
    setup(**conf)
