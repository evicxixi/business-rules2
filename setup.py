# -*- coding: utf-8 -*-

from setuptools import setup, find_packages  # type: ignore

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='business-rules2',
    version='1.1.4',
    author='Laurenz Spanner',
    author_email='laurenz.sp@gmail.com',
    description='Python DSL for setting up business intelligence rules that can be configured without code',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords="business rules engine",
    python_requires='>= 3.6',
    packages=find_packages(exclude=("tests",)),  # type: ignore
    url="https://business-rules2.readthedocs.io/",
    project_urls={
        'Source': 'https://github.com/laurenz-sp/business-rules2/business-rules2',
        'Tracker': 'https://github.com/laurenz-sp/business-rules2/issues',
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    install_requires=[
        'pyparsing'
        'parsimonious'
    ],
    extras_require={
        'dev': [
            'pytest',
            'mock'
        ]
    }
)
