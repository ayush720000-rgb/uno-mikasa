#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Styled message blocks for everything that is not gameplay.

The helpers escape their text, so player names can never break the HTML.
``send_async`` switches to HTML mode automatically for ``HTMLText``.
"""

import html


class HTMLText(str):
    """A string that is already safe, ready-to-send Telegram HTML."""


def _esc(text):
    return html.escape(str(text), quote=False)


def block(icon, text, title=None):
    """A notice. Short notices are one bold line; a title adds a heading above
    a blockquote, so a notice never looks like a lone quoted sentence."""
    if title:
        return HTMLText("<b>%s %s</b>\n\n<blockquote>%s</blockquote>"
                        % (icon, _esc(title), _esc(text)))
    return HTMLText("%s <b>%s</b>" % (icon, _esc(text)))


def ok(text, title=None):
    return block("✅", text, title)


def warn(text, title=None):
    return block("⚠️", text, title)


def info(text, title=None):
    return block("ℹ️", text, title)
