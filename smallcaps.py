#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert text to ꜱᴍᴀʟʟ ᴄᴀᴘꜱ without breaking anything functional.

Only plain ASCII letters are converted. These are left untouched:
  * HTML tags and entities       <b>, <a href="...">, &amp;
  * format placeholders          {name}, {0}, %s, %(name)s
  * bot commands                 /join, /new
  * @mentions                    @mybot
  * URLs                         https://example.com

Names and other values that are inserted later with ``str.format`` are not
part of the text, so they keep their normal look.
"""

import re

from config import SMALL_CAPS

_NORMAL = "abcdefghijklmnopqrstuvwxyz"
# Unicode has no small-cap "x", so it stays as it is.
_SMALL = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"

assert len(_NORMAL) == len(_SMALL) == 26

_TABLE = str.maketrans(_NORMAL + _NORMAL.upper(), _SMALL * 2)

_PROTECTED = re.compile(
    r"""
      <[^>]+>                          # HTML tags
    | &[A-Za-z]+;|&\#\d+;             # HTML entities
    | \{[^{}]*\}                       # str.format placeholders
    | %\([^)]*\)[sdr]|%[sdr]           # printf-style placeholders
    | https?://[^\s<>"']+              # URLs
    | (?<![\w/])/[A-Za-z_]\w*          # /commands
    | @\w+                             # @mentions
    """,
    re.VERBOSE,
)


def small_caps(text):
    """Return ``text`` in small caps, leaving protected parts unchanged."""
    if not text:
        return text

    out = []
    last = 0
    for match in _PROTECTED.finditer(text):
        out.append(text[last:match.start()].translate(_TABLE))
        out.append(match.group(0))
        last = match.end()
    out.append(text[last:].translate(_TABLE))
    return "".join(out)


if __name__ == "__main__":
    import sys

    print(small_caps(" ".join(sys.argv[1:]) or "Hello from the UNO bot! /join"))


def themed(text):
    """Display text: small caps when SMALL_CAPS is on, unchanged otherwise"""
    return small_caps(text) if SMALL_CAPS else text
