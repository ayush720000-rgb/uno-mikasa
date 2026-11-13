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
from pony.orm import db_session
import html
import os
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

from config import MIN_PLAYERS, DEFAULT_GAMEMODE
from user_setting import UserSetting
from utils import send_async, StyledButton, TIMEOUT
from ephemeral import send_command_reply
import system_info
from shared_vars import dispatcher

@db_session
def welcome_handler(update: Update, context: CallbackContext):
    """Handler for /start in a private chat"""
    bot = context.bot
    welcome_text = themed("""🃏 <b>Welcome to {name}</b>

<blockquote>Play the classic UNO card game with your friends, right inside Telegram groups. No setup, no extra apps, just cards.</blockquote>

<b>🚀 Quick Start</b>
<blockquote>1️⃣ Add me to a group
2️⃣ Start a game with /new and let your friends /join
3️⃣ Press /start once two or more players have joined</blockquote>

💡 Need the full guide? Send /help
""").format(name=html.escape(bot.first_name or "UNO"))

    add_button = InlineKeyboardButton(
        text="➕ " + themed("Add me to your group"),
        url="https://t.me/{}?startgroup=true".format(bot.username))

    send_async(bot, update.message.chat_id, text=welcome_text,
               parse_mode=ParseMode.HTML, disable_web_page_preview=True,
               reply_markup=InlineKeyboardMarkup([[add_button]]))


GUIDE_PREFIX = 'guide:'
GUIDE_SECTIONS = ('quick', 'play', 'commands', 'creator', 'modes', 'stats')

PING_REFRESH = 'ping:refresh'

_GAMEMODE_NAMES = {'classic': 'Classic', 'fast': 'Sanic',
                   'wild': 'Wild', 'text': 'Text'}


def _guide_text(section, bot):
    """Text of one guide page. ``menu`` is the front page."""
    username = bot.username
    name = html.escape(bot.first_name or "UNO")

    if section == 'quick':
        return themed("""🚀 <b>Quick Start</b>

<blockquote>1️⃣ Add me to a group
2️⃣ Send /new, then everyone else sends /join
3️⃣ Once {players} or more players have joined, send /start
4️⃣ Type @{username} and a space to play your cards</blockquote>

<blockquote>💡 Send /close once everyone is in, so nobody else joins.</blockquote>
""").format(players=MIN_PLAYERS, username=username)

    if section == 'play':
        return themed("""🎴 <b>How to Play</b>

<b>🃏 Your cards</b>
<blockquote>◆ Type @{username} and a space to see your cards
◆ Tap a card to play it. It must match the color, number or symbol of the last card
◆ Greyed-out cards can't be played right now</blockquote>

<b>⏳ On your turn</b>
<blockquote>◆ Draw first if you have no match, then tap <b>Pass</b> to end your turn
◆ Stack a +2 on another +2 to pass the penalty on
◆ Wild and +4 cards open a color menu
◆ Call a bluff on a +4: if its player had a matching color, they draw 4. Otherwise you draw 6</blockquote>

When it's your turn, tap <b>Make your choice!</b> under the latest message.
{name} also reacts when you play action and wild cards 🎉
""").format(username=username, name=name)

    if section == 'commands':
        return themed("""🎮 <b>Commands</b>

<b>🎲 Playing</b>
<blockquote>/join – join the current game, even mid-game
/leave – leave the game
/skip – skip a player who has run out of time</blockquote>

<b>📊 Your account</b>
<blockquote>/stats – your statistics
/settings – how statistics work
/notify_me – get a private message when a new game starts here</blockquote>

<b>ℹ️ Info</b>
<blockquote>/modes – explain the game modes
/ping – bot status and speed
/about – about this bot
/help – open this guide</blockquote>
""")

    if section == 'creator':
        return themed("""👑 <b>Creator &amp; Moderation</b>

<b>🎬 Starting</b>
<blockquote>/start – start once enough players have joined
/forcestart – start right away and close the lobby (creator or admins)</blockquote>

<b>🛠 Managing</b>
<blockquote>/close and /open – stop or allow new players to join (creator only)
/kick – reply to a player's message with /kick to remove them (creator or admins)
/end or /kill – end the game (creator or admins)</blockquote>

<blockquote>🔑 The bot's host can also list global admins who manage every game.</blockquote>
""")

    if section == 'modes':
        default_mode = _GAMEMODE_NAMES.get(DEFAULT_GAMEMODE, DEFAULT_GAMEMODE)
        return themed("""🎨 <b>Game Modes</b>

<blockquote>🎻 <b>Classic</b> – the conventional UNO deck, no auto-skip
🚀 <b>Sanic</b> – slow players are skipped automatically
🐉 <b>Wild</b> – more special cards, less number variety, no auto-skip
✍️ <b>Text</b> – the conventional UNO deck, played with text instead of stickers</blockquote>

<b>Changing the mode</b>
Before the game starts, the creator types @{username} and a space, then picks a mode.

<blockquote>New games start in <b>{mode}</b> mode unless the host changed the default.</blockquote>
""").format(username=username, mode=default_mode)

    if section == 'stats':
        return themed("""📊 <b>Stats</b>

<blockquote>📈 Statistics are always on and count every game you play.
📊 Check yours any time with /stats</blockquote>

<b>What is tracked</b>
<blockquote>🎮 Games played
🥇 First places and win rate
🃏 Cards played</blockquote>

<b>Playing in several groups</b>
<blockquote>If you are in more than one game, tap the <i>Current game</i> button in the inline menu, then pick the group in the private chat that opens.</blockquote>
""")

    # Front page
    return themed("""🃏 <b>{name} Guide</b>

Play UNO with your friends right inside Telegram groups.
Pick a topic below to learn more.

<blockquote>🚀 <b>Quick Start</b> · your first game in four steps
🎴 <b>How to Play</b> · turns, cards and options
🎮 <b>Commands</b> · everything you can type
👑 <b>Creator &amp; Moderation</b> · run the game
🎨 <b>Game Modes</b> · Classic, Sanic, Wild and Text
📊 <b>Stats</b> · your games at a glance</blockquote>
""").format(name=name)


def _guide_keyboard(section, bot):
    """Inline buttons for one guide page. ``menu`` is the front page.

    Most buttons stay transparent (no style); only the add-to-group button is green.
    """
    if section == 'menu':
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(themed("Quick Start"), callback_data=GUIDE_PREFIX + 'quick'),
             InlineKeyboardButton(themed("How to Play"), callback_data=GUIDE_PREFIX + 'play')],
            [InlineKeyboardButton(themed("Commands"), callback_data=GUIDE_PREFIX + 'commands'),
             InlineKeyboardButton(themed("Creator"), callback_data=GUIDE_PREFIX + 'creator')],
            [InlineKeyboardButton(themed("Game Modes"), callback_data=GUIDE_PREFIX + 'modes'),
             InlineKeyboardButton(themed("Stats"), callback_data=GUIDE_PREFIX + 'stats')],
            [StyledButton(themed("Add me to your group"), style='success',
                          url="https://t.me/{}?startgroup=true".format(bot.username))],
        ])

    index = GUIDE_SECTIONS.index(section)
    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton(themed("Prev"),
                                        callback_data=GUIDE_PREFIX + GUIDE_SECTIONS[index - 1]))
    nav.append(InlineKeyboardButton(themed("Menu"), callback_data=GUIDE_PREFIX + 'menu'))
    if index < len(GUIDE_SECTIONS) - 1:
        nav.append(InlineKeyboardButton(themed("Next"),
                                        callback_data=GUIDE_PREFIX + GUIDE_SECTIONS[index + 1]))
    return InlineKeyboardMarkup([nav])


@db_session
def help_handler(update: Update, context: CallbackContext):
    """Handler for the /help and /guide commands: opens the interactive guide"""
    send_command_reply(context.bot, update.message,
               text=_guide_text('menu', context.bot),
               parse_mode=ParseMode.HTML, disable_web_page_preview=True,
               reply_markup=_guide_keyboard('menu', context.bot))


@db_session
def guide_callback(update: Update, context: CallbackContext):
    """Handler for the guide buttons: switches pages by editing the message"""
    query = update.callback_query
    section = query.data[len(GUIDE_PREFIX):]
    if section != 'menu' and section not in GUIDE_SECTIONS:
        section = 'menu'

    context.bot.answerCallbackQuery(query.id)
    try:
        context.bot.editMessageText(chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    text=_guide_text(section, context.bot),
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True,
                                    reply_markup=_guide_keyboard(section, context.bot))
    except BadRequest as e:
        # Tapping the button of the page that is already open changes nothing
        if 'not modified' not in str(e).lower():
            raise


def _ping_text(bot):
    """Live status message for /ping (plain text, styled labels)"""
    api_ms = None
    started = time.perf_counter()
    try:
        bot.get_me(timeout=TIMEOUT)
        api_ms = (time.perf_counter() - started) * 1000
    except TelegramError:
        pass

    return system_info.render_status(
        username=bot.username,
        uptime=system_info.uptime_seconds(),
        ram=system_info.ram_percent(),
        cpu=system_info.cpu_percent(),
        disk=system_info.disk_percent(),
        api_ms=api_ms)


def _ping_keyboard():
    return InlineKeyboardMarkup([[StyledButton("Refresh", style='success',
                                              callback_data=PING_REFRESH)]])


def ping_handler(update: Update, context: CallbackContext):
    """Handler for the /ping command: shows bot and server status"""
    send_command_reply(context.bot, update.message,
               text=_ping_text(context.bot),
               reply_markup=_ping_keyboard(),
               reply_to_message_id=update.message.message_id)


def ping_callback(update: Update, context: CallbackContext):
    """Handler for the Refresh button under /ping"""
    query = update.callback_query
    context.bot.answerCallbackQuery(query.id, text="Refreshed")
    try:
        context.bot.editMessageText(chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    text=_ping_text(context.bot),
                                    reply_markup=_ping_keyboard())
    except BadRequest as e:
        if 'not modified' not in str(e).lower():
            raise


def _about_text(bot):
    name = system_info.styled(bot.first_name or "UNO")
    tagline = system_info.styled("Your UNO table, right inside Telegram", italic=True)
    return (
        "✦ <b>{name}</b>\n\n"
        "<blockquote>{tagline}\n"
        "Play UNO with friends in any group. No setup, no extra apps, just cards."
        "</blockquote>\n\n"
        "◆ Play inline: your cards live in the message box\n"
        "✦ Stickers for every UNO card\n"
        "➤ Four modes: Classic, Sanic, Wild and Text\n"
        "❖ Live status with /ping\n"
        "\n"
        "<i>Made with care ♡</i>"
    ).format(name=html.escape(name), tagline=html.escape(tagline))


DEV_CONTACT_URL = os.getenv("DEV_CONTACT_URL", "").strip() or "https://t.me/Sexiest_Banda"


def _about_keyboard():
    return InlineKeyboardMarkup([[StyledButton("Dev", style='danger', url=DEV_CONTACT_URL)]])


def about_handler(update: Update, context: CallbackContext):
    """Handler for the /about command"""
    send_command_reply(context.bot, update.message,
               text=_about_text(context.bot),
               parse_mode=ParseMode.HTML, disable_web_page_preview=True,
               reply_markup=_about_keyboard())


@db_session
def modes(update: Update, context: CallbackContext):
    """Handler for the /modes command"""
    modes_explanation = themed("""🎴 <b>Game Modes</b>

<blockquote>🎻 <b>Classic</b> – the conventional UNO deck, no auto skip
🚀 <b>Sanic</b> – the conventional UNO deck, slow players are skipped automatically
🐉 <b>Wild</b> – more special cards, less number variety, no auto skip
✍️ <b>Text</b> – the conventional UNO deck, but played with text instead of stickers</blockquote>

<b>Changing the mode</b>
To change the game mode, the <b>game creator</b> types the bot nickname and a space, just like when playing a card, and all game mode options will appear.
""")
    send_command_reply(context.bot, update.message, text=modes_explanation,
               parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@db_session
def stats(update: Update, context: CallbackContext):
    """Handler for /stats: shows the sender's statistics straight away"""
    user = update.message.from_user
    us = UserSetting.get(id=user.id) or UserSetting(id=user.id)

    games = us.games_played
    wins = us.first_places
    cards = us.cards_played
    rate = round((wins / games) * 100) if games else 0

    games_line = themed("{number} game played" if games == 1 else "{number} games played").format(number=games)
    wins_line = themed("{number} first place ({percent}%)" if wins == 1
                       else "{number} first places ({percent}%)").format(number=wins, percent=rate)
    cards_line = themed("{number} card played" if cards == 1 else "{number} cards played").format(number=cards)

    text = (
        "📊 <b>" + themed("Your Statistics") + "</b>\n"
        "<i>" + html.escape(user.first_name or "") + "</i>\n\n"
        "<b>🏆 " + themed("Results") + "</b>\n"
        "<blockquote>🎮 " + games_line + "\n🥇 " + wins_line + "</blockquote>\n\n"
        "<b>🎴 " + themed("Activity") + "</b>\n"
        "<blockquote>🃏 " + cards_line + "</blockquote>"
    )
    send_command_reply(context.bot, update.message, text=text, parse_mode=ParseMode.HTML)


def register():
    dispatcher.add_handler(CommandHandler('help', help_handler))
    dispatcher.add_handler(CommandHandler('guide', help_handler))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('modes', modes))
    dispatcher.add_handler(CallbackQueryHandler(guide_callback, pattern=r'^guide:'))
    dispatcher.add_handler(CommandHandler('ping', ping_handler))
    dispatcher.add_handler(CommandHandler('about', about_handler))
    dispatcher.add_handler(CallbackQueryHandler(ping_callback, pattern=r'^ping:refresh$'))
