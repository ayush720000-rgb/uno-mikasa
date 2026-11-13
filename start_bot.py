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

# Startup sequence. Besides polling for updates this also makes the bot happy on
# hosts like Render:
#   * a tiny HTTP server on $PORT (web services must listen on a port)
#   * a keep-alive ping so a free web service does not fall asleep
#   * the command menu is set automatically from commandlist.txt

import logging
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import asyncio

from telegram import BotCommand

import tgbridge
from ephemeral import set_command_menu

from config import PORT, KEEPALIVE_URL, KEEPALIVE_INTERVAL, SMALL_CAPS
from smallcaps import small_caps

logger = logging.getLogger(__name__)


class _HealthHandler(BaseHTTPRequestHandler):
    def _respond(self, body=True):
        payload = b"UNO bot is running"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if body:
            self.wfile.write(payload)

    def do_GET(self):
        self._respond()

    def do_HEAD(self):
        self._respond(body=False)

    def log_message(self, *args):  # keep the logs clean
        pass


def _serve_health(port):
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
        logger.info("Health server listening on 0.0.0.0:%s", port)
        server.serve_forever()
    except Exception:
        logger.exception("Health server crashed")


def _keep_alive(url, interval):
    """Ping our own public URL so Render's free tier doesn't spin us down."""
    url = url.rstrip("/") + "/health"
    time.sleep(60)
    while True:
        try:
            urllib.request.urlopen(url, timeout=15).read()
            logger.info("Keep-alive ping ok")
        except Exception as e:
            logger.warning("Keep-alive ping failed: %s", e)
        time.sleep(interval)


def _set_command_menu(bot):  # bot is a tgbridge.SyncBot
    """Fill the Telegram command menu from commandlist.txt (no BotFather needed)"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "commandlist.txt")
    try:
        commands = []
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if " - " not in line:
                    continue
                name, description = line.split(" - ", 1)
                description = description.strip()
                if SMALL_CAPS:
                    description = small_caps(description)
                commands.append(BotCommand(name.strip(), description[:256]))
        set_command_menu(bot, commands)
        logger.info("Command menu set (%d commands)", len(commands))
    except Exception:
        logger.exception("Could not set the command menu")


def start_bot(app):
    async def post_init(application):
        tgbridge.set_loop(asyncio.get_running_loop())
        await asyncio.to_thread(_set_command_menu, tgbridge.SyncBot(application.bot))

    app.post_init = post_init

    if PORT:
        threading.Thread(target=_serve_health, args=(int(PORT),),
                         daemon=True).start()

    if KEEPALIVE_URL:
        threading.Thread(target=_keep_alive,
                         args=(KEEPALIVE_URL, KEEPALIVE_INTERVAL),
                         daemon=True).start()

    # Updates that piled up while the bot was offline are dropped, so players
    # don't get a flood of old commands after a restart.
    app.run_polling(drop_pending_updates=True)
