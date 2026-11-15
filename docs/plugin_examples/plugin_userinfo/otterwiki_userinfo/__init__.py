#!/usr/bin/env python3
# vim: set et ts=8 sts=4 sw=4 ai:

"""
User Info Plugin for An Otter Wiki

This plugin displays the logged-in user in the navbar, see
https://github.com/redimp/otterwiki/issues/574

Features:
- Shows the name, the email, the initial or the initials of the logged-in
  user in the navbar, optionally with the Gravatar icon of the user
- Marks admin users with a shield icon
- Adds a "Logged in as ..." line to the top of the navbar dropdown menu
- Provides an admin page to configure the plugin, the settings are
  stored in the Preferences table

This plugin demonstrates:
1. template_html_navbar_inject() - Add content to the navbar
2. template_html_navbar_dropdown_inject() - Add content to the dropdown menu
3. template_html_admin_menu_inject() - Add a link to the admin menu
4. url_admin_request() - Serve an admin page, rendered from the
   template templates/userinfo/settings.html shipped with the plugin
5. template_folders() - Make the templates of the plugin available
6. static_css() - Add css used by the plugin
7. info() and help() - Describe the plugin
"""

import hashlib
import os
import re
import urllib.parse

from flask import g, redirect, render_template, url_for
from flask_login import current_user
from markupsafe import escape

from otterwiki.plugins import hookimpl, plugin_manager

PLUGIN_NAME = "userinfo"
PREFERENCE_PREFIX = "PLUGIN_USERINFO_"

DISPLAY_OPTIONS = [
    ("name", "Name"),
    ("email", "Email address"),
    ("initial", "Initial"),
    ("initials", "Initials"),
    ("none", "Nothing (e.g. only the Gravatar icon)"),
]
GRAVATAR_DEFAULT_OPTIONS = [
    ("mp", "Mystery person"),
    ("identicon", "Identicon"),
    ("monsterid", "Monster"),
    ("wavatar", "Wavatar"),
    ("retro", "Retro"),
    ("robohash", "Robohash"),
]
DEFAULT_SETTINGS = {
    "display": "name",
    "show_admin": True,
    "gravatar": False,
    "gravatar_default": "mp",
}

HELP = """
Displays the logged-in user in the navbar. Depending on the configuration
the name, the email address, the initial or the initials of the user is
displayed,
optionally with the [Gravatar](https://gravatar.com) icon of the user.
Admins can configure the plugin in the Settings via **User Info**.
"""


class UserInfo:
    """
    Plugin that displays the logged-in user in the navbar.
    """

    @hookimpl
    def setup(self, app, db, storage):
        """Initialize the plugin with the core objects."""
        self.app = app
        self.db = db

    @hookimpl
    def template_folders(self):
        """The templates shipped with the plugin."""
        return [os.path.join(os.path.dirname(__file__), "templates")]

    def get_settings(self):
        """
        Read the settings from the Preferences table. The settings are
        read once per request, so that changes are picked up by all
        worker processes.
        """
        settings = g.get("plugin_userinfo_settings")
        if settings is not None:
            return settings
        from otterwiki.models import Preferences

        settings = dict(DEFAULT_SETTINGS)
        entries = Preferences.query.filter(
            Preferences.name.startswith(PREFERENCE_PREFIX)
        ).all()
        for entry in entries:
            key = entry.name[len(PREFERENCE_PREFIX) :].lower()
            if key not in settings:
                continue
            if isinstance(DEFAULT_SETTINGS[key], bool):
                settings[key] = entry.value == "True"
            else:
                settings[key] = entry.value
        g.plugin_userinfo_settings = settings
        return settings

    def save_settings(self, values):
        from otterwiki.models import Preferences

        settings = dict(DEFAULT_SETTINGS)
        display = values.get("display", "")
        if display in [o[0] for o in DISPLAY_OPTIONS]:
            settings["display"] = display
        else:
            settings["display"] = self.get_settings()["display"]
        gravatar_default = values.get("gravatar_default", "")
        if gravatar_default in [o[0] for o in GRAVATAR_DEFAULT_OPTIONS]:
            settings["gravatar_default"] = gravatar_default
        else:
            settings["gravatar_default"] = self.get_settings()[
                "gravatar_default"
            ]
        settings["show_admin"] = values.get("show_admin") == "True"
        settings["gravatar"] = values.get("gravatar") == "True"

        for key, value in settings.items():
            name = PREFERENCE_PREFIX + key.upper()
            entry = Preferences.query.filter_by(name=name).first()
            if entry is None:
                entry = Preferences(name=name)  # pyright: ignore
            entry.value = str(value)
            self.db.session.add(entry)
        self.db.session.commit()
        g.plugin_userinfo_settings = settings

    @staticmethod
    def user_name():
        name = (current_user.name or "").strip()
        if name:
            return name
        return (current_user.email or "").split("@")[0]

    @staticmethod
    def initials(name):
        """
        The first letters of the first and the last word of the name,
        e.g. "Ada King Lovelace" -> "AL" and "john.doe" -> "JD".
        """
        words = [w for w in re.split(r"[\s._-]+", name) if w]
        if not words:
            return ""
        if len(words) == 1:
            return words[0][:1].upper()
        return (words[0][:1] + words[-1][:1]).upper()

    @staticmethod
    def gravatar_url(email, default, size=48):
        digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
        query = urllib.parse.urlencode({"s": size, "d": default})
        return f"https://gravatar.com/avatar/{digest}?{query}"

    @hookimpl
    def template_html_navbar_inject(self, page):
        if not current_user.is_authenticated:
            return None
        settings = self.get_settings()
        name = self.user_name()
        email = current_user.email or ""

        display = settings["display"]
        html = ""
        if settings["gravatar"] and email:
            src = self.gravatar_url(email, settings["gravatar_default"])
            html += f'<img class="userinfo-avatar" src="{escape(src)}" alt="">'
        if display in ["initial", "initials"]:
            # the initials are displayed as a round badge
            if display == "initial":
                badge = name[:1].upper()
            else:
                badge = self.initials(name)
            if badge:
                html += (
                    f'<span class="userinfo-initials">{escape(badge)}</span>'
                )
        if settings["show_admin"] and getattr(current_user, "is_admin", False):
            html += (
                '<i class="fas fa-user-shield userinfo-admin"'
                ' title="Admin"></i>'
            )
        if display == "name":
            text = name
        elif display == "email":
            text = email
        else:
            text = ""
        if text:
            html += (
                '<span class="userinfo-text d-none d-sm-inline">'
                f'{escape(text)}</span>'
            )
        if not html:
            return None

        title = f"{name} <{email}>" if email else name
        return (
            f'<a href="{url_for("settings")}" class="userinfo-navbar mr-5"'
            f' title="{escape(title)}">{html}</a>'
        )

    @hookimpl
    def template_html_navbar_dropdown_inject(self, page):
        if not current_user.is_authenticated:
            return None
        name = escape(self.user_name())
        email = current_user.email or ""
        if email:
            details = f"<strong>{name}</strong><br>{escape(email)}"
        else:
            details = f"<strong>{name}</strong>"
        return (
            '<div class="dropdown-content userinfo-dropdown">'
            f'Logged in as<br>{details}</div>'
            '<div class="dropdown-divider mt-5 mb-5"></div>'
        )

    @hookimpl
    def template_html_admin_menu_inject(self):
        url = url_for(
            "plugin_url_admin_request", name=PLUGIN_NAME, extra="settings"
        )
        return (
            f'<a href="{url}" class="sidebar-link sidebar-link-with-icon">'
            '<span class="sidebar-icon"><i class="fas fa-user-tag"></i>'
            '</span>User Info</a>'
        )

    @hookimpl
    def url_admin_request(self, plugin, extra, method="GET", values=None):
        if plugin != PLUGIN_NAME or extra != "settings":
            return None
        if method == "POST":
            from otterwiki.helper import toast

            self.save_settings(values or {})
            toast("Preferences saved.")
            return redirect(
                url_for(
                    "plugin_url_admin_request",
                    name=PLUGIN_NAME,
                    extra="settings",
                )
            )
        return render_template(
            "userinfo/settings.html",
            title="User Info",
            settings=self.get_settings(),
            display_options=DISPLAY_OPTIONS,
            gravatar_default_options=GRAVATAR_DEFAULT_OPTIONS,
        )

    @hookimpl
    def static_css(self):
        return """
.userinfo-navbar {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    max-width: 20rem;
    white-space: nowrap;
    color: var(--lm-navbar-link-text-color);
}
.dark-mode .userinfo-navbar {
    color: var(--dm-navbar-link-text-color);
}
.userinfo-navbar:hover,
.dark-mode .userinfo-navbar:hover {
    color: var(--primary-color);
    text-decoration: none;
}
.userinfo-avatar,
.userinfo-initials {
    flex-shrink: 0;
    width: 2.8rem;
    height: 2.8rem;
    border-radius: 50%;
}
.userinfo-initials {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background-color: var(--primary-color);
    color: #fff;
    font-size: 1.2rem;
    font-weight: 600;
    letter-spacing: 0.03rem;
    user-select: none;
}
.userinfo-navbar:hover .userinfo-avatar,
.userinfo-navbar:hover .userinfo-initials {
    box-shadow: 0 0 0 0.2rem var(--primary-color);
}
.userinfo-admin {
    font-size: 1.2rem;
    opacity: 0.7;
}
.userinfo-text {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}
.userinfo-dropdown {
    overflow-wrap: anywhere;
}
"""

    @hookimpl
    def info(self):
        return (
            "User Info",
            "Displays the logged-in user in the navbar.",
            "Navigation",
        )

    @hookimpl
    def help(self, plugin):
        if plugin != "User Info":
            return None
        return HELP


plugin_manager.register(UserInfo())
