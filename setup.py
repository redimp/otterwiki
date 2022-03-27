#!/usr/bin/env python

from setuptools import setup, find_packages
from distutils.util import convert_path

with open(convert_path("otterwiki/version.py")) as f:
    exec(f.read())

setup(
    name="otterwiki",
    version=__version__,
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Flask-Login==0.5.0",
        "Flask-Mail==0.9.1",
        "Flask-SQLAlchemy==2.5.1",
        "Flask==2.0.2",
        "Jinja2>=2.9",
        "gitpython",
        "cython",
        "mistune==0.8.4",
        "pygments",
        #        'itsdangerous',
        "Pillow",
        "unidiff",
        "flask-htmlmin",
    ],
    extras_require={
        "dev": [
            "coverage",
            "pytest",
            "black",
            "smtpdfix",
            "filelock",
        ]
    },
)

# vim: set et ts=8 sts=4 sw=4 ai:
