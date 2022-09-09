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
import webbrowser

import tornado.web            # pylint: disable=import-error
import tornado.httpserver     # pylint: disable=import-error
import tornado.ioloop         # pylint: disable=import-error
import tornado.websocket      # pylint: disable=import-error
import tornado.options        # pylint: disable=import-error

import pygal  # pylint: disable=import-error

HERE = os.path.dirname(os.path.abspath(__file__))

DEBUG_LEVEL = "INFO"

WS_URI = r'/websocket'
LISTEN_PORT = 8000
LISTEN_ADDRESS = '127.0.0.1'
# ~ LISTEN_ADDRESS = '*'

# ~ BROWSER = "firefox"
# ~ BROWSER = "chromium"
BROWSER = None

APPLICATION_OPTIONS = dict(
    debug=True,
    autoreload=True,
    template_path=os.path.join(HERE, "..", "..", "templates"),
    compiled_template_cache=False)

class Index(tornado.web.RequestHandler):  # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):

        logging.debug(f"args:{args}, kwargs:{kwargs}")

        self.parent = kwargs.pop('parent')
        super().__init__(*args, **kwargs)

    def get(self):

        model_params = []
        if self.parent:
            backend = self.parent.backend
            model_params = backend.default_model_params

        ctx = {
            'model_params': model_params,
        }

        logging.debug(f"ctx:{ctx}")

        ret = self.render("index.html", **ctx)

        return ret


class WebsockHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):

        logging.debug(f"args:{args}, kwargs:{kwargs}")
        self.parent = kwargs.pop('parent')

        super().__init__(*args, **kwargs)

    def initialize(self):

        if self.parent:
            self.parent.web_socket_channels.append(self)
            logging.debug(f"n. of active web_socket_channels:{len(self.parent.web_socket_channels)}")

    def open(self, *args, **kwargs):

        logging.info(f"args:{args}, kwargs:{kwargs}")
        super().open(args, kwargs)

    async def write_message(self, msg):

        try:
            # ~ logging.info(f"msg:{msg}")
            await super().write_message(msg)
        except BaseException: # pylint: disable=broad-except
            logging.error(traceback.format_exc())

    def on_message(self, message):

        logging.debug(f"message:{message}")

        if self.parent:
            t_ = self.parent.handle_message_from_UI(self, message)
            asyncio.ensure_future(t_)

    def on_close(self):

        if self.parent:
            self.parent.web_socket_channels.remove(self)
            logging.info(f"n. of active web_socket_channels:{len(self.parent.web_socket_channels)}")


class Frontend(tornado.web.Application):

    def __init__(self, settings, backend):

        self.settings = settings
        self.backend = backend

        self.web_socket_channels = []

        url_map = [
            (r"/", Index, {'parent': self}),
            (WS_URI, WebsockHandler, {'parent': self}),
        ]
        super().__init__(url_map, **APPLICATION_OPTIONS)

    async def run(self):

        logging.info("starting tornado webserver on http://{}:{} ...".format(LISTEN_ADDRESS, LISTEN_PORT))
        self.listen(LISTEN_PORT, LISTEN_ADDRESS)

        try:

            if BROWSER is not None:
                logging.warning("starting browser ...")
                try:
                    webbrowser.get(BROWSER).open('http://127.0.0.1:{}'.format(LISTEN_PORT), new=0)
                except:
                    webbrowser.open('http://127.0.0.1:{}'.format(LISTEN_PORT), new=0)

        except BaseException: # pylint: disable=broad-except
            logging.error(traceback.format_exc())

    def refresh_params_panel(self):

        html_ = "<table>"
        for k, p in self.backend.model_params.items():
            html_ += f'<tr><td colspan="3">{k}:</td></tr>'

            html_ += '<tr>'
            for k_ in ('a', 'b', 'c'):
                html_ += f"""
                <td>
                    <label for=""{k}_{k_}"">{k_}:</label>
                    <input type="number" step="0.1" class="model_param" id="{k}_{k_}" value="{p[k_]}"
                     min="0" max="100"
                    onchange="refresh_data_graph();"></input>
                </td>
                """
            html_ += '</tr>'
        html_ += '</table>'

        # ~ logging.info(f"html_:{html_}")

        self.send_message_to_UI("params_container", html_)

    def refresh_data_graph(self):

        data = self.backend.refresh_model_data()

        line_chart = pygal.XY(
            width=900,
            height=500,
            x_label_rotation=30,
            dots_size=0.5,
            stroke_style={'width': .5},
            # ~ stroke=False,
            # ~ show_dots=False,
            # ~ show_legend=False, 
            human_readable=True, 
            legend_at_bottom=True,
            legend_at_bottom_columns=len(data),
            # ~ legend_box_size=40,
            truncate_legend=40,
        )

        line_chart.title = 'plot example (au, au)'
        line_chart.x_labels = [i * 10 for i in range(0, int(len(data[0]) / 10))]

        for line in data:
            label, serie = line
            line_chart.add(label, serie)
        graph_svg = line_chart.render(is_unicode=True)
        self.send_message_to_UI("pygal_data_container", graph_svg)

        # ~ self.send_message_to_UI("altair_data_container", graph_html.decode())

    async def handle_message_from_UI(self, ws_socket, message):

        logging.debug(f"message({type(message)}):{message}")
        message_dict = json.loads(message)

        if message_dict.get("command") == "reset_model_params":

            self.backend.reset_model_params()

            self.refresh_data_graph()
            self.refresh_params_panel()

        elif message_dict.get("command") == "refresh_data_graph":

            params = {}
            for (k, v) in message_dict.get("params", []):
                line_name, param_name = k.split('_')
                params.setdefault(line_name, {})
                params[line_name][param_name] = float(v)

            logging.debug(f"params:{params}")

            self.backend.update_model_params(params)

            self.refresh_data_graph()

        else:
            answer = f"received:{message}"
            innerHTML = "ws_index:{} [{}] {} -> {}".format(
                self.web_socket_channels.index(ws_socket), time.asctime(), message, answer)
            self.send_message_to_UI("answer_display", innerHTML, ws_socket)

    def send_message_to_UI(self, element_id, innerHTML, ws_client=None):

        msg = {"element_id": element_id, "innerHTML": innerHTML}
        msg = json.dumps(msg)

        if ws_client:
            t_ = ws_client.write_message(msg)
            asyncio.ensure_future(t_)

        else:  # broadcast
            for ws_ch in self.web_socket_channels:
                t_ = ws_ch.write_message(msg)
                asyncio.ensure_future(t_)

