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


"""Defines helper functions to build the inline result list"""

from smallcaps import themed
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedSticker as Sticker

import card as c
from utils import display_color, display_color_group, display_name


def add_choose_color(results, game):
    """Add choose color options"""
    for color in c.COLORS:
        results.append(
            InlineQueryResultArticle(
                id=color,
                title=themed("Choose Color"),
                description=display_color(color),
                input_message_content=
                InputTextMessageContent(display_color_group(color, game))
            )
        )


def add_other_cards(player, results, game):
    """Add hand cards when choosing colors"""

    results.append(
        InlineQueryResultArticle(
            "hand",
            title=themed("Card (tap for game state):" if len(player.cards) == 1 else "Cards (tap for game state):"),
            description=', '.join([repr(card) for card in player.cards]),
            input_message_content=game_info(game)
        )
    )


def player_list(game):
    """Generate list of player strings"""
    return [themed("{name} ({number} card)" if len(player.cards) == 1 else "{name} ({number} cards)")
            .format(name=player.user.first_name, number=len(player.cards))
            for player in game.players]


def add_no_game(results):
    """Add text result if user is not playing"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title=themed("You are not playing"),
            input_message_content=
            InputTextMessageContent(themed('Not playing right now. Use /new to '
                                      'start a game or /join to join the '
                                      'current game in this group'))
        )
    )


def add_not_started(results):
    """Add text result if the game has not yet started"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title=themed("The game wasn't started yet"),
            input_message_content=
            InputTextMessageContent(themed('Start the game with /start'))
        )
    )


def add_mode_classic(results):
    """Change mode to classic"""
    results.append(
        InlineQueryResultArticle(
            "mode_classic",
            title=themed("🎻 Classic mode"),
            input_message_content=
            InputTextMessageContent(themed('Classic 🎻'))
        )
    )


def add_mode_fast(results):
    """Change mode to classic"""
    results.append(
        InlineQueryResultArticle(
            "mode_fast",
            title=themed("🚀 Sanic mode"),
            input_message_content=
            InputTextMessageContent(themed('Gotta go fast! 🚀'))
        )
    )


def add_mode_wild(results):
    """Change mode to classic"""
    results.append(
        InlineQueryResultArticle(
            "mode_wild",
            title=themed("🐉 Wild mode"),
            input_message_content=
            InputTextMessageContent(themed('Into the Wild~ 🐉'))
        )
    )


def add_mode_text(results):
    """Change mode to text"""
    results.append(
        InlineQueryResultArticle(
            "mode_text",
            title=themed("✍️ Text mode"),
            input_message_content=
            InputTextMessageContent(themed('Text ✍️'))
        )
    )
    
    
def add_draw(player, results):
    """Add option to draw"""
    n = player.game.draw_counter or 1

    results.append(
        Sticker(
            "draw", sticker_file_id=c.STICKERS['option_draw'],
            input_message_content=
            InputTextMessageContent(('Drawing {number} card' if n == 1 else 'Drawing {number} cards')
                                    .format(number=n))
        )
    )


def add_gameinfo(game, results):
    """Add option to show game info"""

    results.append(
        Sticker(
            "gameinfo",
            sticker_file_id=c.STICKERS['option_info'],
            input_message_content=game_info(game)
        )
    )


def add_pass(results, game):
    """Add option to pass"""
    results.append(
        Sticker(
            "pass", sticker_file_id=c.STICKERS['option_pass'],
            input_message_content=InputTextMessageContent(
                'Pass'
            )
        )
    )


def add_call_bluff(results, game):
    """Add option to call a bluff"""
    results.append(
        Sticker(
            "call_bluff",
            sticker_file_id=c.STICKERS['option_bluff'],
            input_message_content=
            InputTextMessageContent("I'm calling your bluff!")
        )
    )


def add_card(game, card, results, can_play):
    """Add an option that represents a card"""

    if can_play:
        if game.mode != "text":
            results.append(
                Sticker(str(card), sticker_file_id=c.STICKERS[str(card)])
        )
        if game.mode == "text":
            results.append(
                Sticker(str(card), sticker_file_id=c.STICKERS[str(card)], input_message_content=InputTextMessageContent("Card Played: {card}".format(card=repr(card).replace('Draw Four', '+4').replace('Draw', '+2').replace('Colorchooser', 'Color Chooser')))
        ))
    else:
        results.append(
            Sticker(str(uuid4()), sticker_file_id=c.STICKERS_GREY[str(card)],
                    input_message_content=game_info(game))
        )


def game_info(game):
    players = player_list(game)
    return InputTextMessageContent(
        themed("Current player: {name}")
        .format(name=display_name(game.current_player.user)) +
        "\n" +
        themed("Last card: {card}").format(card=repr(game.last_card)) +
        "\n" +
        themed("Player: {player_list}" if len(players) == 1 else "Players: {player_list}")
        .format(player_list=" -> ".join(players))
    )
