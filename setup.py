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
        "Werkzeug==2.0.3",
        "Flask-Login==0.5.0",
        "Flask-Mail==0.9.1",
        "Flask-SQLAlchemy==2.5.1",
        "Flask==2.0.3",
        "Jinja2>=2.9",
        "gitpython",
        "cython",
        "mistune==2.0.4",
        "pygments",
        "Pillow",
        "unidiff",
        "flask-htmlmin==2.2.0",
    ],
    extras_require={
        "dev": [
            "coverage",
            "pytest",
            "black",
            "tox",
        ]
    },
)

# vim: set et ts=8 sts=4 sw=4 ai:
