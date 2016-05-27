#!/usr/bin/env python
# coding=utf-8

from setuptools import setup


# Use semantic versioning: MAJOR.MINOR.PATCH
version = '0.1.6'


def get_requires():
    try:
        with open('requirements.txt', 'r') as f:
            requires = [i for i in map(lambda x: x.strip(), f.readlines()) if i]
        return requires
    except IOError:
        return []


def get_long_description():
    try:
        with open('README.rst', 'r') as f:
            return f.read()
    except IOError:
        return ''


setup(
    # license='License :: OSI Approved :: MIT License',
    name='autotagger',
    version=version,
    author='reorx',
    author_email='novoreorx@gmail.com',
    description='Tag .mp3 and .m4a audio files from iTunes data automatically.',
    url='https://github.com/reorx/autotagger',
    long_description=get_long_description(),
    #packages=[
    #    'autotagger',
    #],
    # Or use (make sure find_packages is imported from setuptools):
    # packages=find_packages()
    # Or if it's a single file package
    py_modules=['autotagger'],
    install_requires=get_requires(),
    # package_data={}
    entry_points={
        'console_scripts': ['autotagger = autotagger:main']
    }
)
