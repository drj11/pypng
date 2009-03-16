# $URL$
# $Rev$

conf = dict(
    name='pypng',
    version='0.0.1',
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
