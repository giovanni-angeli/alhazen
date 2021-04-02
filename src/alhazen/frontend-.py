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

LISTEN_PORT = 8000
LISTEN_ADDRESS = '127.0.0.1'

APPLICATION_OPTIONS = dict(
    debug=True,
    autoreload=True,
    template_path=os.path.join(HERE, "..", "templates"),
    compiled_template_cache=False)

GLOBAL_SERVER_INSTANCE = None

def get_server_instance():

    global GLOBAL_SERVER_INSTANCE  # pylint: disable=global-statement

    if GLOBAL_SERVER_INSTANCE is None:
        GLOBAL_SERVER_INSTANCE = Server()

    return GLOBAL_SERVER_INSTANCE


class HttpHandler(tornado.web.RequestHandler):       # pylint: disable=too-few-public-methods

    def get(self):

        ctx = {
            "title": "Alhazen application",
            "footer": "see: https://en.wikipedia.org/wiki/Ibn_al-Haytham",
        }
        ret = self.render("index.html", **ctx)
        return ret


class WebsockHandler(tornado.websocket.WebSocketHandler):

    def initialize(self):

        a = get_server_instance()
        a.web_socket_channels.append(self)
        logging.info(f"n. of active web_socket_channels:{len(a.web_socket_channels)}")

    def open(self, *args, **kwargs):

        super().open(args, kwargs)
        logging.info(f"")

    def on_message(self, message):

        a = get_server_instance()
        t_ = a.handle_message_from_UI(self, message)
        asyncio.ensure_future(t_)

    def on_close(self):

        a = get_server_instance()
        a.web_socket_channels.remove(self)
        logging.info(f"n. of active web_socket_channels:{len(a.web_socket_channels)}")


class Server:

    url_map = [
        (r"/", HttpHandler, {}),
        (r'/websocket', WebsockHandler, {}),
    ]

    web_socket_channels = []
    who_is_locking = []
    waiting_worker_ids = []

    running_workers = {}

    async def wait_for_condition(self,  # pylint: disable=too-many-arguments
                                 condition, extra_info=None, timeout=10, stability_count=2, step=0.1):

        ret = None
        t0 = time.time()
        counter = 0
        try:
            while time.time() - t0 < timeout:

                if condition and condition():
                    counter += 1
                    if counter >= stability_count:
                        ret = True
                        break
                else:
                    counter = 0

                await asyncio.sleep(step)

            if not ret:
                _ = f"timeout expired! timeout:{timeout}.\n"
                if extra_info:
                    _ += str(extra_info)
                logging.info(_)

        except Exception:  # pylint: disable=broad-except
            logging.error(traceback.format_exc())

        return ret

    async def get_from_single_lockable_resource(self, task_id):

        ret = None

        try:

            def condition():
                return not self.who_is_locking

            self.waiting_worker_ids.append(task_id)
            r = await self.wait_for_condition(condition, timeout=10, step=.001, extra_info=f"task_id:{task_id} ")
            self.waiting_worker_ids.remove(task_id)

            if r:
                self.who_is_locking.append(task_id)
                logging.debug(
                    f"who_is_locking:{str(self.who_is_locking).ljust(20)}, waiting_worker_ids:{self.waiting_worker_ids}")
                assert len(self.who_is_locking) == 1
                assert self.who_is_locking not in self.waiting_worker_ids

                await asyncio.sleep(.001)
                ret = content_producer()
                await asyncio.sleep(.001)

                self.who_is_locking.remove(task_id)
                logging.debug(
                    f"who_is_locking:{str(self.who_is_locking).ljust(20)}, waiting_worker_ids:{self.waiting_worker_ids}")
                assert len(self.who_is_locking) == 0

                await asyncio.sleep(.00001)

        except Exception:    # pylint: disable=broad-except
            logging.error(traceback.format_exc())

        return ret

    async def handle_message_from_UI(self, ws_socket, message):

        index_ = self.web_socket_channels.index(ws_socket)

        logging.info(f"index_:{index_}, message:{message}")

        answer = await self.get_from_single_lockable_resource(-1)

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

    def start_tornado(self):

        logging.info("starting tornado webserver on http://{}:{}...".format(LISTEN_ADDRESS, LISTEN_PORT))

        app = tornado.web.Application(self.url_map, **APPLICATION_OPTIONS)
        app.listen(LISTEN_PORT, LISTEN_ADDRESS)
        tornado.platform.asyncio.AsyncIOMainLoop().install()


    def __init__(self):

        self.start_tornado()
        self.start_backend_workers(n_of_workers)



