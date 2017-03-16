#!/usr/bin/env python

from distutils.core import setup

try:
    import pypandoc
    longdesc = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    longdesc = open('README.md').read()

setup(
    name='python-dali',
    version='0.3b',
    description='Interface to DALI lighting systems',
    author='Stephen Early',
    author_email='steve@assorted.org.uk',
    url='https://github.com/sde1000/python-dali',
    download_url='https://github.com/dgomes/python-dali/archive/python-dali-0.3.tar.gz',
    long_description=longdesc,
    packages=[
        'dali',
        'dali.device',
        'dali.driver',
        'dali.gear'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    license='LGPL3+',
    keywords='lighting DALI development',
)
