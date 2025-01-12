#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:
import sys

from otterwiki.server import db
from datetime import datetime, UTC

__all__ = ['Preferences', 'Drafts', 'User', 'migrate_database']


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
    password_hash = db.Column(db.String(512), default="")
    first_seen = db.Column(TimeStamp())
    last_seen = db.Column(TimeStamp())
    is_approved = db.Column(db.Boolean(), default=False)
    is_admin = db.Column(db.Boolean(), default=False)
    email_confirmed = db.Column(db.Boolean(), default=False)
    allow_read = db.Column(db.Boolean(), default=False)
    allow_write = db.Column(db.Boolean(), default=False)
    allow_upload = db.Column(db.Boolean(), default=False)
    provider = db.Column(db.String(8), default="local")

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
        return f"<User {self.id} '{self.name} <{self.email}>' {permissions} {self.provider}>"


def migrate_database():
    # An Otter Wiki <= 2.8.0 has no column User.provider check if the colum exists
    # This has been tested with sqlite3, mariadb 11, postgres 17.
    table_name = db.engine.dialect.identifier_preparer.quote("user")
    try:
        result = db.session.execute(
            db.text(f"SELECT * FROM {table_name} WHERE 0 = 1;")
        )
        user_columns = list(result.keys())
    except:
        user_columns = []
    if 'provider' not in user_columns:
        column_type = User.provider.type.compile(db.engine.dialect)
        column_name = db.engine.dialect.identifier_preparer.quote("provider")
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} NOT NULL DEFAULT 'local';"
        try:
            db.session.execute(db.text(sql))
            db.session.commit()
        except Exception as e:
            print(
                "*** *** *** *** *** *** *** *** *** *** *** *** *** *** ***",
                file=sys.stderr,
            )
            print(
                "*** Fatal Error: Database migration failed.", file=sys.stderr
            )
            print(
                "*** Please upon up an issue in https://github.com/redimp/otterwiki/issues",
                file=sys.stderr,
            )
            print("*** and report the exception:", file=sys.stderr)
            print(e, file=sys.stderr)
            print(
                "*** *** *** *** *** *** *** *** *** *** *** *** *** *** ***",
                file=sys.stderr,
            )
            sys.exit(1)
        print("migrate_database(): added column user.provider")
