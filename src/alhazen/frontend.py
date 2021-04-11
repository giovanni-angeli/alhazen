# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=logging-format-interpolation
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

import os
import time
import asyncio
import logging
import traceback
import json

import tornado.web            # pylint: disable=import-error
import tornado.httpserver     # pylint: disable=import-error
import tornado.ioloop         # pylint: disable=import-error
import tornado.websocket      # pylint: disable=import-error
import tornado.options        # pylint: disable=import-error

import pygal # pylint: disable=import-error


HERE = os.path.dirname(os.path.abspath(__file__))

DEBUG_LEVEL = "INFO"

WS_URI = r'/websocket'
LISTEN_PORT = 8000
# ~ LISTEN_ADDRESS = '127.0.0.1'
LISTEN_ADDRESS = '*'

APPLICATION_OPTIONS = dict(
    debug=True,
    autoreload=True,
    template_path=os.path.join(HERE, "..", "..", "templates"),
    compiled_template_cache=False)


class Index(tornado.web.RequestHandler):  # pylint: disable=too-few-public-methods

    frontend_instance = None

    def get(self):

        model_params = []
        if self.frontend_instance:
            backend = self.frontend_instance.context['backend']
            model_params = backend.default_model_params

        ctx = {
            'model_params': model_params,
        }

        logging.info(f"ctx:{ctx}")

        ret = self.render("index.html", **ctx)

        return ret


class WebsockHandler(tornado.websocket.WebSocketHandler):

    frontend_instance = None

    def initialize(self):

        if self.frontend_instance:
            self.frontend_instance.web_socket_channels.append(self)
            logging.info(f"n. of active web_socket_channels:{len(self.frontend_instance.web_socket_channels)}")

    def open(self, *args, **kwargs):

        super().open(args, kwargs)
        logging.info(f"")

    def on_message(self, message):

        logging.info(f"message:{message}")

        if self.frontend_instance:
            t_ = self.frontend_instance.handle_message_from_UI(self, message)
            asyncio.ensure_future(t_)

    def on_close(self):

        if self.frontend_instance:
            self.frontend_instance.web_socket_channels.remove(self)
            logging.info(f"n. of active web_socket_channels:{len(self.frontend_instance.web_socket_channels)}")


class Frontend(tornado.web.Application):

    def __init__(self):

        self.web_socket_channels = []

        class WebsockHandler_(WebsockHandler):
            frontend_instance = self

        class Index_(Index): # pylint: disable=too-few-public-methods
            frontend_instance = self

        url_map = [
            (r"/", Index_, {}),
            (WS_URI, WebsockHandler_, {}),
        ]
        super().__init__(url_map, **APPLICATION_OPTIONS)

    async def run(self):

        logging.info("starting tornado webserver on http://{}:{}...".format(LISTEN_ADDRESS, LISTEN_PORT))
        self.listen(LISTEN_PORT, LISTEN_ADDRESS)
        tornado.platform.asyncio.AsyncIOMainLoop().install()

    def __refresh_params_panel(self):

        html_ = ""
        for k, p in self.context['backend'].model_params.items():
            html_ += f'{k}:<br></br>'
            for k_ in ('a', 'b', 'c'):
                html_ += f"""
                    <label>{k_}:</label>
                    <input type="number" step="0.1" class="model_param" id="{k}_{k_}" value="{p[k_]}" 
                     min="0" max="100"
                    onchange="refresh_data_graph();"></input>
                """
            html_ += '<br></br>'

        # ~ logging.info(f"html_:{html_}")

        self.send_message_to_UI("params_container", html_)

    def __refresh_data_graph(self):

        data = self.context['backend'].refresh_model_data()

        line_chart = pygal.XY(width=900, height=500)
        line_chart.title = 'semi-random data (au, au)'
        line_chart.x_labels = [i * 10 for i in range(0, int(len(data[0])/10))]

        for line in data:
            line_chart.add(*line)
        graph_html = line_chart.render()
        self.send_message_to_UI("pushed_data_container", graph_html.decode())

    async def handle_message_from_UI(self, ws_socket, message):

        index_ = self.web_socket_channels.index(ws_socket)
        logging.info(f"index_:{index_}, message({type(message)}):{message}")
        message_dict = json.loads(message)

        if message_dict.get("command") == "reset_model_params":

            self.context['backend'].reset_model_params()

            self.__refresh_data_graph()
            self.__refresh_params_panel()

        elif message_dict.get("command") == "refresh_data_graph":

            params = {}
            for (k, v) in message_dict.get("params", []):
                line_name, param_name = k.split('_')
                params.setdefault(line_name, {})
                params[line_name][param_name] = float(v)

            logging.info(f"params:{params}")

            self.context['backend'].update_model_params(params)

            self.__refresh_data_graph()
            self.__refresh_params_panel()

        else:
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
