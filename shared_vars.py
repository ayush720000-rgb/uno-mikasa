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


from config import TOKEN, WORKERS
import os
from telegram.ext import Application
import tgbridge

from game_manager import GameManager
from database import db
# The UserSetting table must be defined before db.generate_mapping() runs below.
# Importing it later (e.g. from simple_commands) crashes startup with an ERDiagramError.
import user_setting  # noqa: F401

if not TOKEN:
    raise SystemExit(
        "TOKEN is not set. Get a token from @BotFather and set it as the "
        "TOKEN environment variable (on Render: Environment tab -> TOKEN).")

db.bind('sqlite', os.getenv('UNO_DB', 'uno.sqlite3'), create_db=True)
db.generate_mapping(create_tables=True)

gm = GameManager()
app = Application.builder().token(TOKEN).concurrent_updates(WORKERS).build()
dispatcher = tgbridge.Dispatcher(app)
