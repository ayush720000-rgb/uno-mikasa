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

from pony.orm import db_session
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext

from fmt import info
from shared_vars import dispatcher
from smallcaps import themed
from utils import send_async


@db_session
def show_settings(update: Update, context: CallbackContext):
    """Handler for /settings: explains what is configurable (statistics are always on)"""
    chat = update.message.chat

    text = info(themed("Statistics are always on, so every game you play is counted."))
    send_async(context.bot, chat.id,
               text=text + "\n\n" + themed("See your numbers with /stats"),
               parse_mode=ParseMode.HTML)


def register():
    dispatcher.add_handler(CommandHandler('settings', show_settings))
