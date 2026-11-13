#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram bot to play UNO in group chats
# Copyright (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from smallcaps import themed
import html
import logging
from telegram import InlineKeyboardButton

from fmt import HTMLText
from mwt import MWT
from shared_vars import gm
import tgbridge

logger = logging.getLogger(__name__)

TIMEOUT = 2.5


class StyledButton(InlineKeyboardButton):
    """Inline button that can carry Telegram's color style.

    style: 'primary' (blue), 'success' (green) or 'danger' (red). None keeps
    the default transparent look, which is what most buttons should use.
    """

    def __init__(self, text, style=None, **kwargs):
        super().__init__(text, style=style, **kwargs)


def display_name(user):
    """Plain name for status text. No @username, so nothing looks like a tag."""
    return user.first_name or "Player"


def mention(user):
    """Clickable name for HTML messages. Works even when the player has no username."""
    name = html.escape(user.first_name or "Player", quote=False)
    return HTMLText('<a href="tg://user?id=%d">%s</a>' % (user.id, name))


def display_color(color):
    """ Convert a color code to actual color name """
    if color == "r":
        return themed("{emoji} Red").format(emoji='❤️')
    if color == "b":
        return themed("{emoji} Blue").format(emoji='💙')
    if color == "g":
        return themed("{emoji} Green").format(emoji='💚')
    if color == "y":
        return themed("{emoji} Yellow").format(emoji='💛')


def display_color_group(color, game):
    """ Convert a color code to actual color name """
    if color == "r":
        return "{emoji} Red".format(
            emoji='❤️')
    if color == "b":
        return "{emoji} Blue".format(
            emoji='💙')
    if color == "g":
        return "{emoji} Green".format(
            emoji='💚')
    if color == "y":
        return "{emoji} Yellow".format(
            emoji='💛')


def error(update, context, exc=None):
    """Simple error handler. ``exc`` lets helpers report an exception directly."""
    err = exc if exc is not None else getattr(context, 'error', None)
    logger.error("Unhandled error: %s", err, exc_info=err)


def send_async(bot, *args, **kwargs):
    """Send a message without waiting for the reply"""
    if isinstance(kwargs.get('text'), HTMLText):
        kwargs.setdefault('parse_mode', 'HTML')
    tgbridge.fire(bot, 'sendMessage', *args, **kwargs)


def answer_async(bot, *args, **kwargs):
    """Answer an inline query without waiting for the reply"""
    tgbridge.fire(bot, 'answerInlineQuery', *args, **kwargs)


def game_is_running(game):
    return game in gm.chatid_games.get(game.chat.id, list())


def user_is_creator(user, game):
    return user.id in game.owner


def user_is_admin(user, bot, chat):
    return user.id in get_admin_ids(bot, chat.id)


def user_is_creator_or_admin(user, game, bot, chat):
    return user_is_creator(user, game) or user_is_admin(user, bot, chat)


@MWT(timeout=60*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
