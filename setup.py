#!/usr/bin/env python

from distutils.core import setup

setup(
    name='dali',
    version='0.1',
    description='Interface to DALI lighting systems',
    author='Stephen Early',
    author_email='steve@greenend.org.uk',
    url='https://github.com/sde1000/python-dali',
    packages=[
        'dali',
        'dali.device',
        'dali.driver',
        'dali.gear'
    ],
)
