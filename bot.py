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
import logging
from datetime import datetime

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.constants import ParseMode
from telegram.ext import InlineQueryHandler, ChosenInlineResultHandler, \
    CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters

import card as c
import settings
import simple_commands
from actions import do_skip, do_play_card, do_draw, do_call_bluff, start_player_countdown
from config import WAITING_TIME, DEFAULT_GAMEMODE, MIN_PLAYERS
from errors import (NoGameInChatError, LobbyClosedError, AlreadyJoinedError,
                    NotEnoughPlayersError, DeckEmptyError)
from fmt import ok, warn, info, HTMLText
from results import (add_call_bluff, add_choose_color, add_draw, add_gameinfo,
                     add_no_game, add_other_cards, add_pass,
                     add_card, add_mode_classic, add_mode_fast, add_mode_wild, add_mode_text)
from shared_vars import gm, app, dispatcher
from tgbridge import background
from simple_commands import help_handler, welcome_handler
from start_bot import start_bot
from utils import display_name, mention
from utils import send_async, answer_async, error, TIMEOUT, user_is_creator_or_admin, game_is_running


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

@db_session
def notify_me(update: Update, context: CallbackContext):
    """Handler for /notify_me command, pm people for next game"""
    chat_id = update.message.chat_id
    if update.message.chat.type == 'private':
        send_async(context.bot,
                   chat_id,
                   text=info(themed("Send this command in a group to be notified "
                          "when a new game is started there.")))
    else:
        try:
            gm.remind_dict[chat_id].add(update.message.from_user.id)
        except KeyError:
            gm.remind_dict[chat_id] = {update.message.from_user.id}


@db_session
def new_game(update: Update, context: CallbackContext):
    """Handler for the /new command"""
    chat_id = update.message.chat_id

    if update.message.chat.type == 'private':
        help_handler(update, context)

    else:

        if update.message.chat_id in gm.remind_dict:
            for user in gm.remind_dict[update.message.chat_id]:
                send_async(context.bot,
                           user,
                           text=ok(themed("A new game has been started in {title}").format(
                                title=update.message.chat.title)))

            del gm.remind_dict[update.message.chat_id]

        game = gm.new_game(update.message.chat)
        game.starter = update.message.from_user
        game.owner.append(update.message.from_user.id)
        game.mode = DEFAULT_GAMEMODE
        send_async(context.bot, chat_id,
                   text=ok(themed("Created a new game! Join the game with /join "
                          "and start the game with /start")))


@db_session
def kill_game(update: Update, context: CallbackContext):
    """Handler for the /kill command"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    if not games:
            send_async(context.bot, chat.id,
                       text=warn(themed("There is no running game in this chat.")))
            return

    game = games[-1]

    if user_is_creator_or_admin(user, game, context.bot, chat):

        try:
            gm.end_game(chat, user)
            send_async(context.bot, chat.id, text="Game ended!")

        except NoGameInChatError:
            send_async(context.bot, chat.id,
                       text=warn(themed("The game is not started yet. "
                              "Join the game with /join and start the game with /start")),
                       reply_to_message_id=update.message.message_id)

    else:
        send_async(context.bot, chat.id,
                  text=warn(themed("Only the game creator ({name}) and admin can do that.").format(name=game.starter.first_name)),
                  reply_to_message_id=update.message.message_id)

@db_session
def join_game(update: Update, context: CallbackContext):
    """Handler for the /join command"""
    chat = update.message.chat

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    try:
        gm.join_game(update.message.from_user, chat)

    except LobbyClosedError:
            send_async(context.bot, chat.id, text=warn(themed("The lobby is closed")))

    except NoGameInChatError:
        send_async(context.bot, chat.id,
                   text=warn(themed("No game is running at the moment. "
                          "Create a new game with /new")),
                   reply_to_message_id=update.message.message_id)

    except AlreadyJoinedError:
        send_async(context.bot, chat.id,
                   text=warn(themed("You already joined the game. Start the game "
                          "with /start")),
                   reply_to_message_id=update.message.message_id)

    except DeckEmptyError:
        send_async(context.bot, chat.id,
                   text=warn(themed("There are not enough cards left in the deck for "
                          "new players to join.")),
                   reply_to_message_id=update.message.message_id)

    else:
        send_async(context.bot, chat.id,
                   text=ok(themed("Joined the game")),
                   reply_to_message_id=update.message.message_id)


@db_session
def leave_game(update: Update, context: CallbackContext):
    """Handler for the /leave command"""
    chat = update.message.chat
    user = update.message.from_user

    player = gm.player_for_user_in_chat(user, chat)

    if player is None:
        send_async(context.bot, chat.id, text=warn(themed("You are not playing in a game in "
                                        "this group.")),
                   reply_to_message_id=update.message.message_id)
        return

    game = player.game
    user = update.message.from_user

    try:
        gm.leave_game(user, chat)

    except NoGameInChatError:
        send_async(context.bot, chat.id, text=warn(themed("You are not playing in a game in "
                                        "this group.")),
                   reply_to_message_id=update.message.message_id)

    except NotEnoughPlayersError:
        gm.end_game(chat, user)
        send_async(context.bot, chat.id, text="Game ended!")

    else:
        if game.started:
            send_async(context.bot, chat.id,
                       text=HTMLText("Okay. Next Player: {name}".format(
                           name=mention(game.current_player.user))),
                       reply_to_message_id=update.message.message_id)
        else:
            send_async(context.bot, chat.id,
                       text="{name} left the game before it started.".format(
                           name=display_name(user)),
                       reply_to_message_id=update.message.message_id)


@db_session
def kick_player(update: Update, context: CallbackContext):
    """Handler for the /kick command"""

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    chat = update.message.chat
    user = update.message.from_user

    try:
        game = gm.chatid_games[chat.id][-1]

    except (KeyError, IndexError):
            send_async(context.bot, chat.id,
                   text=warn(themed("No game is running at the moment. "
                          "Create a new game with /new")),
                   reply_to_message_id=update.message.message_id)
            return

    if not game.started:
        send_async(context.bot, chat.id,
                   text=warn(themed("The game is not started yet. "
                          "Join the game with /join and start the game with /start")),
                   reply_to_message_id=update.message.message_id)
        return

    if user_is_creator_or_admin(user, game, context.bot, chat):

        if update.message.reply_to_message:
            kicked = update.message.reply_to_message.from_user

            try:
                gm.leave_game(kicked, chat)

            except NoGameInChatError:
                send_async(context.bot, chat.id, text=warn(themed("Player {name} is not found in the current game.").format(name=display_name(kicked))),
                                reply_to_message_id=update.message.message_id)
                return

            except NotEnoughPlayersError:
                gm.end_game(chat, user)
                send_async(context.bot, chat.id,
                                text=ok(themed("{0} was kicked by {1}").format(display_name(kicked), display_name(user))))
                send_async(context.bot, chat.id, text="Game ended!")
                return

            send_async(context.bot, chat.id,
                            text=ok(themed("{0} was kicked by {1}").format(display_name(kicked), display_name(user))))

        else:
            send_async(context.bot, chat.id,
                text=warn(themed("Please reply to the person you want to kick and type /kick again.")),
                reply_to_message_id=update.message.message_id)
            return

        send_async(context.bot, chat.id,
                   text=HTMLText("Okay. Next Player: {name}".format(
                       name=mention(game.current_player.user))),
                   reply_to_message_id=update.message.message_id)

    else:
        send_async(context.bot, chat.id,
                  text=warn(themed("Only the game creator ({name}) and admin can do that.").format(name=game.starter.first_name)),
                  reply_to_message_id=update.message.message_id)


def select_game(update: Update, context: CallbackContext):
    """Handler for callback queries to select the current game"""

    chat_id = int(update.callback_query.data)
    user_id = update.callback_query.from_user.id
    players = gm.userid_players.get(user_id, list())
    for player in players:
        if player.game.chat.id == chat_id:
            gm.userid_current[user_id] = player
            break
    else:
        context.bot.answerCallbackQuery(update.callback_query.id)
        send_async(context.bot,
                   update.callback_query.message.chat_id,
                   text=warn(themed("Game not found.")))
        return

    def selected():
        back = [[InlineKeyboardButton(text=themed("Back to last group"),
                                      switch_inline_query='')]]
        context.bot.answerCallbackQuery(update.callback_query.id,
                                text=themed("Please switch to the group you selected!"),
                                show_alert=False,
                                timeout=TIMEOUT)

        context.bot.editMessageText(chat_id=update.callback_query.message.chat_id,
                            message_id=update.callback_query.message.message_id,
                            text=themed("Selected group: {group}\n"
                                   "<b>Make sure that you switch to the correct "
                                   "group!</b>").format(
                                group=gm.userid_current[user_id].game.chat.title),
                            reply_markup=InlineKeyboardMarkup(back),
                            parse_mode=ParseMode.HTML,
                            timeout=TIMEOUT)

    background(selected)


@db_session
def status_update(update: Update, context: CallbackContext):
    """Remove player from game if user leaves the group"""
    chat = update.message.chat

    if update.message.left_chat_member:
        user = update.message.left_chat_member

        player = gm.player_for_user_in_chat(user, chat)
        if player is None:
            return

        try:
            gm.leave_game(user, chat)

        except NoGameInChatError:
            pass
        except NotEnoughPlayersError:
            gm.end_game(chat, user)
            send_async(context.bot, chat.id, text="Game ended!")
        else:
            send_async(context.bot, chat.id, text="Removing {name} from the game"
                       .format(name=display_name(user)))


def _begin_game(context, chat, game):
    """Deals the hands and posts the first card and player"""
    game.start()

    for player in game.players:
        player.draw_first_hand()
    choice = [[InlineKeyboardButton(text="Make your choice!", switch_inline_query_current_chat='')]]
    first_message = HTMLText(
        "First player: {name}\n"
           "Use /close to stop people from joining the game."
        .format(name=mention(game.current_player.user)))

    def send_first():
        """Send the first card and player"""

        context.bot.sendSticker(chat.id,
                        sticker=c.STICKERS[str(game.last_card)],
                        timeout=TIMEOUT)

        context.bot.sendMessage(chat.id,
                        text=first_message,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(choice),
                        timeout=TIMEOUT)

    background(send_first)
    start_player_countdown(context.bot, game, context.job_queue)


@db_session
def force_start(update: Update, context: CallbackContext):
    """Handler for the /forcestart command: starts at once, closing the lobby"""
    chat = update.message.chat
    user = update.message.from_user

    if chat.type == 'private':
        send_async(context.bot, chat.id,
                   text=warn(themed("Use /forcestart in a group.")))
        return

    try:
        game = gm.chatid_games[chat.id][-1]
    except (KeyError, IndexError):
        send_async(context.bot, chat.id,
                   text=warn(themed("There is no game running in this chat. Create "
                              "a new one with /new")),
                   reply_to_message_id=update.message.message_id)
        return

    if game.started:
        send_async(context.bot, chat.id, text=warn(themed("The game has already started")),
                   reply_to_message_id=update.message.message_id)
        return

    if not user_is_creator_or_admin(user, game, context.bot, chat):
        send_async(context.bot, chat.id,
                   text=warn(themed("Only the game creator ({name}) and admin can do that.").format(name=game.starter.first_name)),
                   reply_to_message_id=update.message.message_id)
        return

    if len(game.players) < MIN_PLAYERS:
        send_async(context.bot, chat.id,
                   text="At least {minplayers} players must /join the game "
                          "before you can start it".format(minplayers=MIN_PLAYERS),
                   reply_to_message_id=update.message.message_id)
        return

    game.open = False
    send_async(context.bot, chat.id,
               text=ok(themed("Starting right now! The lobby is closed.")))
    _begin_game(context, chat, game)


@db_session
def start_game(update: Update, context: CallbackContext):
    """Handler for the /start command"""

    if update.message.chat.type != 'private':
        chat = update.message.chat

        try:
            game = gm.chatid_games[chat.id][-1]
        except (KeyError, IndexError):
            send_async(context.bot, chat.id,
                       text=warn(themed("There is no game running in this chat. Create "
                              "a new one with /new")))
            return

        if game.started:
            send_async(context.bot, chat.id, text=warn(themed("The game has already started")))

        elif len(game.players) < MIN_PLAYERS:
            send_async(context.bot, chat.id,
                       text="At least {minplayers} players must /join the game "
                              "before you can start it".format(minplayers=MIN_PLAYERS))

        else:
            _begin_game(context, chat, game)

    elif len(context.args) and context.args[0] == 'select':
        players = gm.userid_players.get(update.message.from_user.id, list())
        if not players:
            send_async(context.bot, update.message.chat_id,
                       text=warn(themed("You are not playing in any game right now.")))
            return

        groups = list()
        for player in players:
            title = player.game.chat.title

            if player == gm.userid_current.get(update.message.from_user.id):
                title = '- %s -' % player.game.chat.title

            groups.append(
                [InlineKeyboardButton(text=title,
                                      callback_data=str(player.game.chat.id))]
            )

        send_async(context.bot, update.message.chat_id,
                   text=info(themed('Please select the group you want to play in.')),
                   reply_markup=InlineKeyboardMarkup(groups))

    else:
        welcome_handler(update, context)


@db_session
def close_game(update: Update, context: CallbackContext):
    """Handler for the /close command"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=warn(themed("There is no running game in this chat.")))
        return

    game = games[-1]

    if user.id in game.owner:
        game.open = False
        send_async(context.bot, chat.id, text=ok(themed("Closed the lobby. "
                                        "No more players can join this game.")))
        return

    else:
        send_async(context.bot, chat.id,
                   text=warn(themed("Only the game creator ({name}) and admin can do that.").format(name=game.starter.first_name)),
                   reply_to_message_id=update.message.message_id)
        return


@db_session
def open_game(update: Update, context: CallbackContext):
    """Handler for the /open command"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=warn(themed("There is no running game in this chat.")))
        return

    game = games[-1]

    if user.id in game.owner:
        game.open = True
        send_async(context.bot, chat.id, text=ok(themed("Opened the lobby. "
                                        "New players may /join the game.")))
        return
    else:
        send_async(context.bot, chat.id,
                   text=warn(themed("Only the game creator ({name}) and admin can do that.").format(name=game.starter.first_name)),
                   reply_to_message_id=update.message.message_id)
        return


@db_session
def skip_player(update: Update, context: CallbackContext):
    """Handler for the /skip command"""
    chat = update.message.chat
    user = update.message.from_user

    player = gm.player_for_user_in_chat(user, chat)
    if not player:
        send_async(context.bot, chat.id,
                   text=warn(themed("You are not playing in a game in this chat.")))
        return

    game = player.game
    skipped_player = game.current_player

    started = skipped_player.turn_started
    now = datetime.now()
    delta = (now - started).seconds

    # You can't skip if the current player still has time left
    # You can skip yourself even if you have time left (you'll still draw)
    if delta < skipped_player.waiting_time and player != skipped_player:
        n = skipped_player.waiting_time - delta
        send_async(context.bot, chat.id,
                   text=("Please wait {time} second" if n == 1 else "Please wait {time} seconds")
                   .format(time=n),
                   reply_to_message_id=update.message.message_id)
    else:
        do_skip(context.bot, player)


@db_session
def reply_to_query(update: Update, context: CallbackContext):
    """
    Handler for inline queries.
    Builds the result list for inline queries and answers to the client.
    """
    results = list()
    switch = None

    try:
        user = update.inline_query.from_user
        user_id = user.id
        players = gm.userid_players[user_id]
        player = gm.userid_current[user_id]
        game = player.game
    except KeyError:
        add_no_game(results)
    else:

        # The game has not started.
        # The creator may change the game mode, other users just get a "game has not started" message.
        if not game.started:
            # Any joined player can pick the game mode before the game starts.
            add_mode_classic(results)
            add_mode_fast(results)
            add_mode_wild(results)
            add_mode_text(results)


        elif user_id == game.current_player.user.id:
            if game.choosing_color:
                add_choose_color(results, game)
                add_other_cards(player, results, game)
            else:
                if not player.drew:
                    add_draw(player, results)

                else:
                    add_pass(results, game)

                if game.last_card.special == c.DRAW_FOUR and game.draw_counter:
                    add_call_bluff(results, game)

                playable = player.playable_cards()
                added_ids = list()  # Duplicates are not allowed

                for card in sorted(player.cards):
                    add_card(game, card, results,
                             can_play=(card in playable and
                                            str(card) not in added_ids))
                    added_ids.append(str(card))

                add_gameinfo(game, results)

        elif user_id != game.current_player.user.id or not game.started:
            for card in sorted(player.cards):
                add_card(game, card, results, can_play=False)

        else:
            add_gameinfo(game, results)

        for result in results:
            # PTB 22 objects are frozen; the id is set on the object directly
            object.__setattr__(result, 'id', result.id + ':%d' % player.anti_cheat)

        if players and game and len(players) > 1:
            switch = themed('Current game: {game}').format(game=game.chat.title)

    answer_async(context.bot, update.inline_query.id, results, cache_time=0,
                 switch_pm_text=switch, switch_pm_parameter='select')


@db_session
def process_result(update: Update, context: CallbackContext):
    """
    Handler for chosen inline results.
    Checks the players actions and acts accordingly.
    """
    try:
        user = update.chosen_inline_result.from_user
        player = gm.userid_current[user.id]
        game = player.game
        result_id = update.chosen_inline_result.result_id
        chat = game.chat
    except (KeyError, AttributeError):
        return

    logger.debug("Selected result: " + result_id)

    result_id, anti_cheat = result_id.split(':')
    last_anti_cheat = player.anti_cheat
    player.anti_cheat += 1

    if result_id in ('hand', 'gameinfo', 'nogame'):
        return
    elif result_id.startswith('mode_'):
        # First 5 characters are 'mode_', the rest is the gamemode.
        mode = result_id[5:]
        game.set_mode(mode)
        logger.info("Gamemode changed to {mode}".format(mode = mode))
        send_async(context.bot, chat.id, text="Gamemode changed to {mode}".format(mode=mode))
        return
    elif len(result_id) == 36:  # UUID result
        return
    elif int(anti_cheat) != last_anti_cheat:
        send_async(context.bot, chat.id,
                   text="Cheat attempt by {name}"
                   .format(name=display_name(player.user)))
        return
    elif result_id == 'call_bluff':
        reset_waiting_time(context.bot, player)
        do_call_bluff(context.bot, player)
    elif result_id == 'draw':
        reset_waiting_time(context.bot, player)
        do_draw(context.bot, player)
    elif result_id == 'pass':
        game.turn()
    elif result_id in c.COLORS:
        game.choose_color(result_id)
    else:
        reset_waiting_time(context.bot, player)
        do_play_card(context.bot, player, result_id)

    if game_is_running(game):
        nextplayer_message = HTMLText(
            "Next player: {name}"
            .format(name=mention(game.current_player.user)))
        choice = [[InlineKeyboardButton(text="Make your choice!", switch_inline_query_current_chat='')]]
        send_async(context.bot, chat.id,
                        text=nextplayer_message,
                        reply_markup=InlineKeyboardMarkup(choice))
        start_player_countdown(context.bot, game, context.job_queue)


# UNO card stickers, keyed by sticker file_unique_id -> card name (e.g. "r_draw").
# file_id changes when a sticker is sent inline, file_unique_id does not.
# The option stickers (draw, pass, bluff, info) are sent as text, not stickers.
CARD_STICKER_NAMES = {
    c.sticker_unique_id(file_id): name
    for name, file_id in c.STICKERS.items()
    if name not in c.STICKERS_OPTIONS
}
CARD_STICKER_NAMES.pop(None, None)


def _sticker_reaction(card):
    """Mikasa's reply for a played card, or None to stay quiet"""
    key = card.special or card.value

    if key == c.DRAW_TWO:
        return "Ouch, +2 for the next player! 😬"
    if key == c.SKIP:
        return "Skip! The next player sits this one out. ⏭️"
    if key == c.REVERSE:
        return "Reverse! The order just flipped. 🔄"
    if key == c.DRAW_FOUR:
        return "+4! Someone is about to get a big hand. 😈"
    if key == c.CHOOSE:
        return "Wild! Pick a color. 🎨"

    # Number cards are frequent, so they get no reply.
    return None


@db_session
def card_sticker_reaction(update: Update, context: CallbackContext):
    """Reacts to UNO card stickers that were played through inline mode.

    Origin: the sticker message must be sent via this bot (``via_bot``), so
    ordinary stickers from users and the bot's own stickers are ignored.
    Update type: a plain ``message`` update with a sticker, not a
    ``chosen_inline_result``. Game logic stays in ``process_result``.
    """
    message = update.message
    sticker = message.sticker
    via_me = message.via_bot is not None and message.via_bot.id == context.bot.id

    # Diagnostics: one line per sticker so the logs show whether inline stickers
    # arrive at all and whether their file_id matches a known card.
    name = CARD_STICKER_NAMES.get(sticker.file_unique_id)
    logger.info("Sticker in chat %s: via_bot=%s card=%s file_id=%s unique_id=%s",
                message.chat_id, via_me, name, sticker.file_id, sticker.file_unique_id)

    if not via_me or name is None:
        return

    text = _sticker_reaction(c.from_str(name))
    if text:
        send_async(context.bot, message.chat_id, text=text,
                   reply_to_message_id=message.message_id)


def reset_waiting_time(bot, player):
    """Resets waiting time for a player and sends a notice to the group"""
    chat = player.game.chat

    if player.waiting_time < WAITING_TIME:
        player.waiting_time = WAITING_TIME
        send_async(bot, chat.id,
                   text="Waiting time for {name} has been reset to {time} "
                           "seconds"
                   .format(name=display_name(player.user), time=WAITING_TIME))


# Add all handlers to the dispatcher and run the bot
dispatcher.add_handler(InlineQueryHandler(reply_to_query))
dispatcher.add_handler(ChosenInlineResultHandler(process_result))
dispatcher.add_handler(CallbackQueryHandler(select_game, pattern=r'^-?\d+$'))
dispatcher.add_handler(CommandHandler('start', start_game))
dispatcher.add_handler(CommandHandler('forcestart', force_start))
dispatcher.add_handler(CommandHandler('new', new_game))
dispatcher.add_handler(CommandHandler('kill', kill_game))
dispatcher.add_handler(CommandHandler('end', kill_game))
dispatcher.add_handler(CommandHandler('join', join_game))
dispatcher.add_handler(CommandHandler('leave', leave_game))
dispatcher.add_handler(CommandHandler('kick', kick_player))
dispatcher.add_handler(CommandHandler('open', open_game))
dispatcher.add_handler(CommandHandler('close', close_game))
dispatcher.add_handler(CommandHandler('skip', skip_player))
dispatcher.add_handler(CommandHandler('notify_me', notify_me))
simple_commands.register()
settings.register()
dispatcher.add_handler(MessageHandler(filters.Sticker.ALL, card_sticker_reaction))
dispatcher.add_handler(MessageHandler(filters.StatusUpdate.ALL, status_update))
dispatcher.add_error_handler(error)

start_bot(app)
