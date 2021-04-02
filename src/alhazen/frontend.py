# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=logging-format-interpolation
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

import sys
import os
import time
import asyncio
import logging
import traceback
import json
import random

import tornado.web            # pylint: disable=import-error
import tornado.httpserver     # pylint: disable=import-error
import tornado.ioloop         # pylint: disable=import-error
import tornado.websocket      # pylint: disable=import-error
import tornado.options        # pylint: disable=import-error

HERE = os.path.dirname(os.path.abspath(__file__))

DEBUG_LEVEL = "INFO"

WS_URI = r'/websocket'
LISTEN_PORT = 8000
LISTEN_ADDRESS = '127.0.0.1'

APPLICATION_OPTIONS = dict(
    debug=True,
    autoreload=True,
    template_path=os.path.join(HERE, "..", "..", "templates"),
    compiled_template_cache=False)



_FRONTEND_INSTANCE = None

def get_frontend_instance():
    
    global _FRONTEND_INSTANCE
    return _FRONTEND_INSTANCE

class Index(tornado.web.RequestHandler):       # pylint: disable=too-few-public-methods

    def get(self):

        backend = get_frontend_instance().context['backend']

        ctx = {
            'model_params': backend.model_params,
        }
        ret = self.render("index.html", **ctx)
        return ret


class WebsockHandler(tornado.websocket.WebSocketHandler):

    def initialize(self):

        a = get_frontend_instance()
        a.web_socket_channels.append(self)
        logging.info(f"n. of active web_socket_channels:{len(a.web_socket_channels)}")

    def open(self, *args, **kwargs):

        super().open(args, kwargs)
        logging.info(f"")

    def on_message(self, message):

        a = get_frontend_instance()
        t_ = a.handle_message_from_UI(self, message)
        asyncio.ensure_future(t_)

    def on_close(self):

        a = get_frontend_instance()
        a.web_socket_channels.remove(self)
        logging.info(f"n. of active web_socket_channels:{len(a.web_socket_channels)}")


class Frontend(tornado.web.Application):

    def __init__(self):

        self.web_socket_channels = []

        global _FRONTEND_INSTANCE
        _FRONTEND_INSTANCE = self

        url_map = [
            (r"/", Index, {}),
            (WS_URI, WebsockHandler, {}),
        ]
        super().__init__(url_map, **APPLICATION_OPTIONS)

    async def run(self):

        logging.info("starting tornado webserver on http://{}:{}...".format(LISTEN_ADDRESS, LISTEN_PORT))
        self.listen(LISTEN_PORT, LISTEN_ADDRESS)
        tornado.platform.asyncio.AsyncIOMainLoop().install()

    async def handle_message_from_UI(self, ws_socket, message):

        index_ = self.web_socket_channels.index(ws_socket)

        logging.info(f"index_:{index_}, message:{message}")

        answer = f"received:{message}"

        innerHTML = "ws_index:{} [{}] {} -> {}".format(
            index_, time.asctime(), message, answer)

        self.send_message_to_UI("answer_display", innerHTML)

    def send_message_to_UI(self, element_id, innerHTML, ws_index=None):

        msg = {"element_id": element_id, "innerHTML": innerHTML}
        msg = json.dumps(msg)

        if ws_index:
            t_ = self.web_socket_channels[ws_index].write_message(msg)
            asyncio.ensure_future(t_)

        else:  # broadcast
            for ws_ch in self.web_socket_channels:
                t_ = ws_ch.write_message(msg)
                asyncio.ensure_future(t_)
