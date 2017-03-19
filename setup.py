#!/usr/bin/env python

from setuptools import setup
import unittest

def readme():
    with open('README.rst') as f:
        return f.read()

def test_suite():
    test_loader = unittest.TestLoader()
    return test_loader.discover('dali')

setup(
    name='python-dali',
    version='0.4',
    description='Interface to DALI lighting systems',
    long_description=readme(),
    author='Stephen Early',
    author_email='steve@assorted.org.uk',
    url='https://github.com/sde1000/python-dali',
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
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    license='LGPL3+',
    keywords='lighting DALI development',
    test_suite='setup.test_suite',
)
