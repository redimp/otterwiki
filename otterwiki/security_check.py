#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
otterwiki.security_check

Extensible security check framework for Otterwiki.
Each check is a function registered via the @register_backend_check decorator
that returns a SecurityCheckResult (or a list of) if an issue is found, None otherwise.
"""

import os
import re
import ipaddress

from bs4 import BeautifulSoup
from flask import request
from otterwiki.server import app
from otterwiki.plugins import plugin_manager
from otterwiki.util import empty


class SecurityCheckResult:
    """Represents a single security check result.

    `passed=False` results are issues to display in the issues table
    (severity is required). `passed=True` results are reported under
    the "checks passed" table; severity is ignored there.
    """

    def __init__(self, issue, description, severity=None, passed=False):
        self.issue = issue
        self.description = description
        self.severity = severity
        self.passed = passed

    def to_dict(self):
        d = {
            "issue": self.issue,
            "description": self.description,
            "passed": self.passed,
        }
        if not self.passed:
            d["severity"] = self.severity
        return d


# registry of backend check functions
_backend_checks = []


def register_backend_check(func):
    """Decorator to register a backend security check function."""
    _backend_checks.append(func)
    return func


def run_backend_checks():
    """Run all registered backend security checks.

    Returns a dict ``{"issues": [...], "passed": [...]}`` where each
    entry is the dict produced by :py:meth:`SecurityCheckResult.to_dict`.
    """
    issues = []
    passed = []
    for check_func in _backend_checks:
        try:
            result = check_func()
            if result is None:
                continue
            results = result if isinstance(result, list) else [result]
            for r in results:
                (passed if r.passed else issues).append(r.to_dict())
        except Exception as e:
            app.logger.warning(
                f"Security check '{check_func.__name__}' failed: {e}"
            )
    return {"issues": issues, "passed": passed}


#
# helper functions
#


def _get_custom_dir():
    """Get the custom files directory path, respecting USE_STATIC_PATH env var."""
    return os.path.join(
        os.getenv(
            "USE_STATIC_PATH",
            os.path.join(app.root_path, "static"),
        ),
        "custom",
    )


def _has_css_rules(content):
    """Check if CSS content has actual rules beyond comments and whitespace."""
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = content.strip()
    return bool(content)


def _has_js_code(content):
    """Check if JS content has actual code beyond comments and whitespace."""
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
    content = content.strip()
    return bool(content)


def _has_html_content(content):
    """Check if HTML content has actual content beyond comments and whitespace."""
    soup = BeautifulSoup(content, "html.parser")
    return bool(soup.get_text(strip=True)) or soup.find() is not None


def _is_private_ip(ip_str):
    """Check if an IP address is private or loopback."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


def _is_loopback_host():
    """Return True if the request's Host header points at loopback.

    Used to downgrade severity on local/dev access; the wiki may still be
    reachable via tunnel or port forward, so the downgrade is communicated
    in the description.
    """
    try:
        host = request.host or ""
    except RuntimeError:
        return False
    # strip port
    if host.startswith("[") and "]" in host:
        host = host[1 : host.index("]")]
    elif ":" in host:
        host = host.rsplit(":", 1)[0]
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


_LOOPBACK_NOTE = (
    " <em>Severity reduced because the wiki was accessed via a loopback "
    "host; if this server is reachable from elsewhere, treat this as "
    "critical.</em>"
)


#
# backend security checks
#


@register_backend_check
def check_anonymous_write_access():
    """Check if anonymous users can edit the wiki."""
    if app.config.get("WRITE_ACCESS", "").upper() == "ANONYMOUS":
        loopback = _is_loopback_host()
        description = (
            "Anonymous users have write access to your wiki, allowing anyone "
            "to create or edit pages without logging in. Unless this is "
            "intentional, it is a significant security risk. "
            'This can be changed on the <a href="/-/admin/permissions_and_registration">'
            "Permissions and Registration</a> page."
        )
        if loopback:
            description += _LOOPBACK_NOTE
        return SecurityCheckResult(
            issue="Anonymous users can edit the wiki",
            description=description,
            severity="MEDIUM" if loopback else "CRITICAL",
        )
    return SecurityCheckResult(
        issue="Anonymous write access is disabled",
        description="Write access requires an authenticated account.",
        passed=True,
    )


@register_backend_check
def check_anonymous_upload_access():
    """Check if anonymous users can upload files."""
    if app.config.get("ATTACHMENT_ACCESS", "").upper() == "ANONYMOUS":
        loopback = _is_loopback_host()
        description = (
            "Anonymous users have file upload access to your wiki, allowing "
            "anyone to upload files without logging in. Unless this is "
            "intentional, it is a significant security risk. "
            'This can be changed on the <a href="/-/admin/permissions_and_registration">'
            "Permissions and Registration</a> page."
        )
        if loopback:
            description += _LOOPBACK_NOTE
        return SecurityCheckResult(
            issue="Anonymous users can upload files",
            description=description,
            severity="MEDIUM" if loopback else "CRITICAL",
        )
    return SecurityCheckResult(
        issue="Anonymous upload access is disabled",
        description="Attachment uploads require an authenticated account.",
        passed=True,
    )


@register_backend_check
def check_server_name_not_set():
    """Check if SERVER_NAME is configured."""
    if not app.config.get("SERVER_NAME"):
        return SecurityCheckResult(
            issue="Server name not configured",
            description=(
                "The <code>SERVER_NAME</code> configuration variable is not set. "
                "This may lead to issues depending on your reverse proxy configuration. "
                'See <a href="https://flask.palletsprojects.com/en/stable/config/#SERVER_NAME">'
                "Flask documentation</a> for details. "
                'This can be changed on the <a href="/-/admin">'
                "Application Preferences</a> page."
            ),
            severity="NOTICE",
        )
    return SecurityCheckResult(
        issue="Server name is configured",
        description="The <code>SERVER_NAME</code> configuration variable is set.",
        passed=True,
    )


@register_backend_check
def check_open_registrations():
    """Check if registrations are fully open without any restrictions."""
    if (
        not app.config.get("DISABLE_REGISTRATION", False)
        and not app.config.get("EMAIL_NEEDS_CONFIRMATION", True)
        and app.config.get("AUTO_APPROVAL", True)
    ):
        return SecurityCheckResult(
            issue="Fully open registrations",
            description=(
                "Your wiki allows unlimited registrations without requiring "
                "email confirmation or manual approval. This means anyone can "
                "create accounts without restrictions, potentially flooding the "
                "wiki with spam users. "
                'This can be changed on the <a href="/-/admin/permissions_and_registration">'
                "Permissions and Registration</a> page."
            ),
            severity="HIGH",
        )
    return SecurityCheckResult(
        issue="Registrations are restricted",
        description=(
            "New registrations are disabled or require email confirmation "
            "or manual approval."
        ),
        passed=True,
    )


@register_backend_check
def check_plugins_active():
    """Check if plugins are active."""
    plugin_info = plugin_manager.list_plugin_distinfo()
    if plugin_info:
        plugin_names = [dist.project_name for _, dist in plugin_info]
        return SecurityCheckResult(
            issue="Plugins are active",
            description=(
                "You are using wiki plugins. Note that there are "
                "little to no restrictions on what a plugin can do, and "
                "third-party plugins are not reviewed for security by an Otterwiki "
                "developers. Your active plugins: "
                f"<strong>{', '.join(plugin_names)}</strong>."
            ),
            severity="NOTICE",
        )
    return None


@register_backend_check
def check_custom_css():
    """Check if custom CSS rules are defined."""
    custom_dir = _get_custom_dir()
    css_path = os.path.join(custom_dir, "custom.css")
    try:
        if os.path.exists(css_path):
            with open(css_path, "r") as f:
                content = f.read()
            if _has_css_rules(content):
                return SecurityCheckResult(
                    issue="Custom CSS is being used",
                    description=(
                        "You have custom CSS rules defined in "
                        "<code>custom.css</code>. If this is intentional, "
                        "this notice can be ignored."
                    ),
                    severity="NOTICE",
                )
    except Exception:
        pass
    return None


@register_backend_check
def check_custom_js():
    """Check if custom JavaScript code is defined."""
    custom_dir = _get_custom_dir()
    js_path = os.path.join(custom_dir, "custom.js")
    try:
        if os.path.exists(js_path):
            with open(js_path, "r") as f:
                content = f.read()
            if _has_js_code(content):
                return SecurityCheckResult(
                    issue="Custom JavaScript is being used",
                    description=(
                        "You have custom JavaScript code defined in "
                        "<code>custom.js</code>. If this is intentional, "
                        "this notice can be ignored."
                    ),
                    severity="NOTICE",
                )
    except Exception:
        pass
    return None


@register_backend_check
def check_custom_html():
    """Check if custom HTML content is being used."""
    findings = []
    custom_dir = _get_custom_dir()

    head_path = os.path.join(custom_dir, "customHead.html")
    try:
        if os.path.exists(head_path):
            with open(head_path, "r") as f:
                content = f.read()
            if _has_html_content(content):
                findings.append("customHead.html")
    except Exception:
        pass

    body_path = os.path.join(custom_dir, "customBody.html")
    try:
        if os.path.exists(body_path):
            with open(body_path, "r") as f:
                content = f.read()
            if _has_html_content(content):
                findings.append("customBody.html")
    except Exception:
        pass

    if not empty(app.config.get("HTML_EXTRA_HEAD", "")):
        findings.append("HTML_EXTRA_HEAD")

    if not empty(app.config.get("HTML_EXTRA_BODY", "")):
        findings.append("HTML_EXTRA_BODY")

    if findings:
        return SecurityCheckResult(
            issue="Custom HTML is being used",
            description=(
                "You have custom HTML defined in: <strong>"
                + ", ".join(findings)
                + "</strong>. If this is intentional, this notice can be ignored."
            ),
            severity="NOTICE",
        )
    return None


@register_backend_check
def check_html_whitelist():
    """Check if RENDERER_HTML_ALLOWLIST is configured."""
    if not empty(app.config.get("RENDERER_HTML_ALLOWLIST", "")):
        return SecurityCheckResult(
            issue="Custom HTML allowlist is configured",
            description=(
                "Your <code>RENDERER_HTML_ALLOWLIST</code> is not empty, which "
                "allows potentially unsafe additional HTML tags and attributes "
                "in wiki content. If this is intentional, this notice can be "
                "ignored."
            ),
            severity="NOTICE",
        )
    return None


@register_backend_check
def check_reverse_proxy():
    """Check for missing or misconfigured reverse proxy.

    Triggers in these cases:
    - Request from a non-private IP with no proxy headers > likely no reverse proxy at all
    - X-Forwarded-For present but X-Forwarded-Proto missing > incomplete proxy setup
    """
    has_real_ip = bool(request.headers.get("X-Real-IP"))
    has_forwarded_for = bool(request.headers.get("X-Forwarded-For"))
    has_forwarded_proto = bool(request.headers.get("X-Forwarded-Proto"))
    has_proxy_headers = has_real_ip or has_forwarded_for or has_forwarded_proto
    remote_addr = request.remote_addr
    is_private = _is_private_ip(remote_addr)

    # direct local access without any proxy headers is likely fine
    if is_private and not has_proxy_headers:
        return None

    issues = []
    issue_title = "Misconfigured reverse proxy"

    # non-private IP with no proxy headers
    if not is_private and not has_proxy_headers:
        issue_title = "Missing or misconfigured reverse proxy"
        issues.append(
            "Your wiki is directly accessible from the internet without a "
            "reverse proxy or the reverse proxy is misconfigured. "
            "This is not recommended as it exposes the "
            "application server directly."
        )

    # X-Forwarded-For present but X-Forwarded-Proto missing
    if has_forwarded_for and not has_forwarded_proto:
        issues.append(
            "<code>X-Forwarded-For</code> is present but "
            "<code>X-Forwarded-Proto</code> is not, so the wiki cannot "
            "determine the original protocol."
        )

    if issues:
        # HIGH severity if we suspect no reverse proxy exists at all
        suspected_no_proxy = not is_private and not has_proxy_headers
        # HIGH severity if there is a proxy but X-Forwarded-Proto is missing
        proxy_without_proto = has_proxy_headers and not has_forwarded_proto

        severity = (
            "HIGH" if (suspected_no_proxy or proxy_without_proto) else "MEDIUM"
        )

        issues_list = "".join(f"<li>{issue}</li>" for issue in issues)
        return SecurityCheckResult(
            issue=issue_title,
            description=(
                "Your wiki does not appear to be running behind a properly "
                "configured reverse proxy:"
                f"<ul>{issues_list}</ul>"
                "Please consult the documentation for "
                '<a href="https://otterwiki.com/Installation#reverse-proxy">'
                "example reverse proxy configurations</a> and "
                '<a href="https://otterwiki.com/Configuration#reverse-proxy-and-ips">'
                "required wiki parameters</a>."
            ),
            severity=severity,
        )

    return SecurityCheckResult(
        issue="Reverse proxy looks correctly configured",
        description="Proxy headers appear consistent.",
        passed=True,
    )
