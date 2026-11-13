#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Bridge between the synchronous bot code and python-telegram-bot 22 (async).
#
# Handlers keep their synchronous style. Each one runs in a worker thread
# (asyncio.to_thread), so pony ORM sessions and the game logic never have to
# span an await. Bot calls made from those threads are handed to the event
# loop with run_coroutine_threadsafe. Old Bot API style names and keyword
# arguments (sendMessage, reply_to_message_id, timeout, ...) are translated to
# python-telegram-bot 22 form here, in one place.

import asyncio
import concurrent.futures
import functools
import inspect
import logging
import re

from telegram import InlineQueryResultsButton, LinkPreviewOptions, ReplyParameters

logger = logging.getLogger(__name__)

MAIN_LOOP = None  # set by start_bot once the event loop is running
_BACKGROUND = concurrent.futures.ThreadPoolExecutor(max_workers=16,
                                                    thread_name_prefix="bg")


def set_loop(loop):
    global MAIN_LOOP
    MAIN_LOOP = loop


def _snake(name):
    """sendMessage -> send_message. Names that are already snake_case pass through."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _translate(kwargs):
    """Map old python-telegram-bot 13 keyword arguments to version 22."""
    kw = dict(kwargs)
    kw.pop("timeout", None)  # per-request timeouts are configured on the Application now
    message_id = kw.pop("reply_to_message_id", None)
    if message_id is not None and "reply_parameters" not in kw:
        kw["reply_parameters"] = ReplyParameters(message_id=message_id,
                                                 allow_sending_without_reply=True)
    if kw.pop("disable_web_page_preview", False):
        kw["link_preview_options"] = LinkPreviewOptions(is_disabled=True)
    # Bot API 6.7 replaced switch_pm_text/switch_pm_parameter with a results button
    switch_text = kw.pop("switch_pm_text", None)
    switch_param = kw.pop("switch_pm_parameter", None)
    if switch_text and "button" not in kw:
        kw["button"] = InlineQueryResultsButton(text=switch_text,
                                                start_parameter=switch_param or "start")
    return kw


def run(coro):
    """Run a bot coroutine on the event loop and wait for its result (from a worker thread)."""
    return asyncio.run_coroutine_threadsafe(coro, MAIN_LOOP).result()


def run_on_loop(fn):
    """Call a plain function on the event loop thread and return its result."""
    future = concurrent.futures.Future()

    def runner():
        try:
            future.set_result(fn())
        except BaseException as exc:  # propagate to the calling thread
            future.set_exception(exc)

    MAIN_LOOP.call_soon_threadsafe(runner)
    return future.result()


def _log_failure(future):
    if future.cancelled():
        return
    exc = future.exception()
    if exc is not None:
        logger.error("Telegram call failed: %s", exc, exc_info=exc)


def submit(coro):
    """Fire and forget a bot coroutine on the event loop."""
    future = asyncio.run_coroutine_threadsafe(coro, MAIN_LOOP)
    future.add_done_callback(_log_failure)


def background(fn, *args):
    """Run a synchronous function in a background thread (replaces dispatcher.run_async)."""
    future = _BACKGROUND.submit(fn, *args)
    future.add_done_callback(_log_failure)
    return future


class SyncBot:
    """Wraps the python-telegram-bot Bot so code in worker threads can call it synchronously."""

    def __init__(self, bot):
        self._bot = bot

    def __getattr__(self, name):
        attr = getattr(self._bot, _snake(name))
        if callable(attr) and inspect.iscoroutinefunction(attr):
            @functools.wraps(attr)
            def call(*args, **kwargs):
                return run(attr(*args, **_translate(kwargs)))
            return call
        return attr  # plain attributes such as username or first_name

    def __eq__(self, other):
        return isinstance(other, SyncBot) and other._bot is self._bot

    def __hash__(self):
        return hash(id(self._bot))


class SyncJobQueue:
    """Schedules jobs from a worker thread (JobQueue must be touched on the loop)."""

    def __init__(self, job_queue):
        self._job_queue = job_queue

    def run_once(self, callback, when, **kwargs):
        return run_on_loop(lambda: self._job_queue.run_once(callback, when, **kwargs))


class SyncContext:
    """Callback context whose bot and job queue can be used from a worker thread."""

    def __init__(self, context):
        self._context = context
        self.bot = SyncBot(context.bot)
        job_queue = context.job_queue
        self.job_queue = SyncJobQueue(job_queue) if job_queue is not None else None

    def __getattr__(self, name):
        return getattr(self._context, name)


def fire(bot, method, *args, **kwargs):
    """Send a bot method without waiting for it (replaces dispatcher.run_async(bot.method))."""
    real = bot._bot if isinstance(bot, SyncBot) else bot
    submit(getattr(real, _snake(method))(*args, **_translate(kwargs)))


def threaded(fn):
    """Wrap a synchronous (update, context) handler so PTB can await it."""
    @functools.wraps(fn)
    async def handler(update, context):
        await asyncio.to_thread(fn, update, SyncContext(context))
    return handler


def threaded_job(fn):
    """Wrap a synchronous job callback (context only) so PTB can await it."""
    @functools.wraps(fn)
    async def job(context):
        await asyncio.to_thread(fn, SyncContext(context))
    return job


class Dispatcher:
    """Stands in for the old dispatcher: registers handlers on the Application."""

    def __init__(self, app):
        self._app = app

    def add_handler(self, handler):
        handler.callback = threaded(handler.callback)
        self._app.add_handler(handler)

    def add_error_handler(self, callback):
        self._app.add_error_handler(threaded(callback))
