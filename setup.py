#!/usr/bin/env python3
from setuptools import setup
import unittest


def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='python-dali',
    version='0.7.1',
    description='Interface to DALI lighting systems',
    long_description=readme(),
    long_description_content_type='text/x-rst',
    author='Stephen Early',
    author_email='steve@assorted.org.uk',
    url='https://github.com/sde1000/python-dali',
    packages=[
        'dali',
        'dali.device',
        'dali.driver',
        'dali.gear',
        'dali.tests',
    ],
    extras_require={
        "driver-unipi": ["pyusb", "pymodbus"],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 3',
    ],
    license='LGPL3+',
    keywords='lighting DALI development',
)
