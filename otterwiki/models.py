#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from otterwiki.server import db
from datetime import datetime, UTC

__all__ = ['Preferences', 'Drafts']


class TimeStamp(db.types.TypeDecorator):
    # thanks to https://mike.depalatis.net/blog/sqlalchemy-timestamps.html
    impl = db.types.DateTime
    LOCAL_TIMEZONE = datetime.now(UTC).astimezone().tzinfo

    def process_bind_param(self, value: datetime, dialect):
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)

        return value.astimezone(UTC)

    def process_result_value(self, value, dialect):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)


class Preferences(db.Model):
    name = db.Column(db.String(256), primary_key=True)
    value = db.Column(db.Text)

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
    datetime = db.Column(TimeStamp())


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    first_seen = db.Column(TimeStamp())
    last_seen = db.Column(TimeStamp())
    is_approved = db.Column(db.Boolean(), default=False)
    is_admin = db.Column(db.Boolean(), default=False)
    email_confirmed = db.Column(db.Boolean(), default=False)
    allow_read = db.Column(db.Boolean(), default=False)
    allow_write = db.Column(db.Boolean(), default=False)
    allow_upload = db.Column(db.Boolean(), default=False)

    def __repr__(self):
        permissions = ""
        if self.allow_read:
            permissions += "R"
        if self.allow_write:
            permissions += "W"
        if self.allow_upload:
            permissions += "U"
        if self.is_admin:
            permissions += "A"
        return f"<User {self.id} '{self.name} <{self.email}>' {permissions}>"
