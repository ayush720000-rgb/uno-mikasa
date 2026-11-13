#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Ephemeral messages (Telegram Bot API 10.2+).
#
# An ephemeral message in a group is visible only to one user and the bot.
# python-telegram-bot 13.x predates this API, so the calls are made directly
# over HTTP with the standard library (no extra dependency).
#
# Flow:
#   1. The command is marked is_ephemeral in the command menu, so the user's
#      command message is only visible to the user and the bot.
#   2. The bot replies with sendMessage + ephemeral_message_parameters, so the
#      reply is only visible to the user who sent the command.

import json
import logging
import urllib.error
import urllib.request

from telegram import InlineKeyboardMarkup

from config import TOKEN, EPHEMERAL_ENABLED, EPHEMERAL_COMMANDS
from fmt import HTMLText
from tgbridge import background
from utils import send_async

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/{method}"
API_TIMEOUT = 10
GROUP_TYPES = ("group", "supergroup")


def _call(method, payload):
    """POST a Bot API method. Raises on any failure; callers decide what to show."""
    req = urllib.request.Request(
        API_URL.format(token=TOKEN, method=method),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if not body.get("ok"):
        raise RuntimeError("%s failed: %s" % (method, body.get("description")))
    return body["result"]


def command_name(text):
    """'/Stats@MyBot extra' -> 'stats'. Empty string when the text is not a command."""
    if not text or not text.startswith("/"):
        return ""
    return text.split()[0][1:].split("@")[0].lower()


def is_ephemeral_for(message):
    """True when this reply should be sent ephemerally."""
    if not EPHEMERAL_ENABLED or message.chat.type not in GROUP_TYPES:
        return False
    return command_name(message.text) in EPHEMERAL_COMMANDS


def set_command_menu(bot, commands):
    """Set the command menu, marking the ephemeral commands with is_ephemeral.

    Falls back to the normal python-telegram-bot call if the API rejects the
    raw request, so the menu is always set.
    """
    if not EPHEMERAL_ENABLED:
        return bot.set_my_commands(commands)
    payload = {
        "commands": [
            {
                "command": c.command,
                "description": c.description,
                "is_ephemeral": c.command in EPHEMERAL_COMMANDS,
            }
            for c in commands
        ]
    }
    try:
        _call("setMyCommands", payload)
    except Exception:
        logger.exception("Raw setMyCommands failed, using the plain command menu")
        bot.set_my_commands(commands)


def _describe(exc):
    """Telegram's own error text, so the log says why a call was rejected."""
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = json.loads(exc.read().decode("utf-8"))
            return "HTTP %s: %s" % (exc.code, body.get("description"))
        except Exception:
            return "HTTP %s" % exc.code
    return str(exc)


def _incoming_ephemeral_id(message):
    """The ephemeral id of the command message. PTB 22 keeps fields it does not know in api_kwargs."""
    return (getattr(message, "api_kwargs", None) or {}).get("ephemeral_message_id")


def _send_ephemeral(bot, message, text, kwargs):
    parse_mode = kwargs.get("parse_mode")
    if parse_mode is None and isinstance(text, HTMLText):
        parse_mode = "HTML"

    payload = {
        "chat_id": message.chat_id,
        "text": str(text),
        "ephemeral_message_parameters": {"receiver_user_id": message.from_user.id},
    }
    thread_id = getattr(message, "message_thread_id", None)
    if thread_id:
        payload["message_thread_id"] = thread_id
    ephemeral_id = _incoming_ephemeral_id(message)
    if ephemeral_id:
        # Reply to the ephemeral command itself, as Telegram's examples do
        payload["reply_parameters"] = {"ephemeral_message_id": ephemeral_id,
                                       "allow_sending_without_reply": True}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if kwargs.get("disable_web_page_preview"):
        payload["link_preview_options"] = {"is_disabled": True}
    markup = kwargs.get("reply_markup")
    if isinstance(markup, InlineKeyboardMarkup):
        payload["reply_markup"] = markup.to_dict()

    try:
        _call("sendMessage", payload)
        return
    except Exception as exc:
        logger.error("Ephemeral reply rejected: %s", _describe(exc))

    if "reply_parameters" in payload:
        # Retry once without the reply link (the link is the part most likely to be rejected)
        payload.pop("reply_parameters")
        try:
            _call("sendMessage", payload)
            return
        except Exception as exc:
            logger.error("Ephemeral retry rejected: %s", _describe(exc))

    # No public fallback: the reply is meant for the sender only, so it is dropped instead.
    logger.error("Reply to /%s was not sent (it would have been public)", command_name(message.text))


def send_command_reply(bot, message, text, **kwargs):
    """Reply to a command. Ephemeral in groups for the commands listed in
    EPHEMERAL_COMMANDS; everywhere else it is a normal reply."""
    if is_ephemeral_for(message):
        background(_send_ephemeral, bot, message, text, kwargs)
    else:
        send_async(bot, message.chat_id, text=text, **kwargs)
