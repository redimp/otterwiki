#!/usr/bin/env python

from otterwiki.server import db

__all__ = ['Preferences']

class Preferences(db.Model):
    name = db.Column(db.String(256), primary_key=True)
    value = db.Column(db.String(256))

    def __str__(self):
        return '{}: {}'.format(self.name, self.value)

class Drafts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pagepath = db.Column(db.String(2048), index=True)
    revision = db.Column(db.String(64))
    author_email = db.Column(db.String(256))
    content = db.Column(db.Text)
    cursor_line = db.Column(db.Integer)
    cursor_ch = db.Column(db.Integer)
    datetime = db.Column(db.DateTime())


