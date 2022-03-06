# An Otter Wiki

An Otter Wiki is a python based software for collaborative content
management, called a [wiki](https://en.wikipedia.org/wiki/Wiki). The
content is stored in a git repository, which keeps track of all changes.
[Markdown](https://daringfireball.net/projects/markdown) is used as
Markup language.

## Quick Start

Create a `settings.cfg` based upon `settings.cfg.skeleton` and set the
variables fitting to your environment. Point the `REPOSITORY` to the
root of the git repository you want to use as wiki. The directory has
to be read- and writeable for the process running the wiki.

Run the application:

    make run

or with debugging enabled

    make debug

And open your browser at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Prerequisites

This is built to be used with Python 3. Update `Makefile` to switch to Python 2
if needed.

Some Flask dependencies are compiled during installation, so `gcc` and Python
header files need to be present. For example, on Ubuntu:

    apt install build-essential python3-dev

## Development environment and release process

 - create virtualenv with Flask and An Otter Wiki installed into it (latter is installed in [develop mode](http://setuptools.readthedocs.io/en/latest/setuptools.html#development-mode) which allows modifying source code directly without a need to re-install the app): `make venv`

 - run development server in debug mode: `make debug`; Flask will restart if source code is modified

 - run tests: `make test` (see also: [Testing Flask Applications](http://flask.pocoo.org/docs/0.12/testing/))

 - to remove virtualenv: `make clean`

 - to modify configuration in development environment: edit file
   `settings.cfg`; this is a local configuration file and it is
*ignored* by Git - make sure to put a proper configuration file to a
production environment when deploying

## Deployment

In either case, generally the idea is to build a package (`make sdist`),
deliver it to a server (`scp ...`), install it (`pip install
otterwiki.tar.gz`), ensure that configuration file exists and
`OTTERWIKI_SETTINGS` environment variable points to it, ensure that user
has access to the working directory to create and write log files in it,
and finally run a [WSGI
container](http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/)
with the application.  And, most likely, it will also run behind a
[reverse
proxy](http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/#proxy-setups).

## Notes

An Otter Wiki is build using multiple tools, frameworks and templates:

 - [purecss.io](https://purecss.io) and the [Responsive Side Menu Layout](https://purecss.io/layouts/).

 - [SimpleMDE](https://simplemde.com/) a beautiful markdown editor.

 - [The flask minimal cookiecutter](https://github.com/candidtim/cookiecutter-flask-minimal).

## Docker

### Build and run using `docker-compose`

Build the latest image using:
```
docker-compose build
```

Optional: configure port and volume storage via the `docker-compose.yml`.

Start the container:
```
docker-compose up -d
```

### Build and run the image manually

First build the image

```
docker build --tag otterwiki:latest .
```

Run the container

```
docker run --name otterwiki -p 80:80 otterwiki:latest
```

Run the container as daemon
```
docker run -d --restart=always -p 80:80 otterwiki
```

 * `-d` runs the Docker container as a daemon in the background.
 * `--restart=always` restarts the container if it crashes, or if the system docker is running on is rebooted.

## MIT License

Copyright (c) 2018-2022 Ralph Thesen <mail@redimp.de>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[modeline]: # ( vim: set fenc=utf-8 spell spl=en sts=4 et tw=72: )
