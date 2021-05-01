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

    frontend_instance = None

    def get(self):

        ret = self.render("index.html")

        return ret


class WebsockHandler(tornado.websocket.WebSocketHandler):

    frontend_instance = None

    def initialize(self):

        if self.frontend_instance:
            self.frontend_instance.web_socket_channels.append(self)
            logging.debug(f"n. of active web_socket_channels:{len(self.frontend_instance.web_socket_channels)}")

    def open(self, *args, **kwargs):

        super().open(args, kwargs)
        logging.debug(f"")

    async def write_message(self, msg):

        try:
            await super().write_message(msg)
        except BaseException: # pylint: disable=broad-except
            logging.error(traceback.format_exc())

    def on_message(self, message):

        logging.debug(f"message:{message}")

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

        class Index_(Index):  # pylint: disable=too-few-public-methods
            frontend_instance = self

        url_map = [
            (r"/", Index_, {}),
            (WS_URI, WebsockHandler_, {}),
        ]
        super().__init__(url_map, **APPLICATION_OPTIONS)

    async def run(self):

        logging.info("starting tornado webserver on http://{}:{} ...".format(LISTEN_ADDRESS, LISTEN_PORT))
        self.listen(LISTEN_PORT, LISTEN_ADDRESS)
        tornado.platform.asyncio.AsyncIOMainLoop().install()

        if BROWSER:
            try:

                logging.info("starting browser ...")
                try:
                    webbrowser.get(BROWSER).open('http://127.0.0.1:{}'.format(LISTEN_PORT), new=0)
                except:
                    webbrowser.open('http://127.0.0.1:{}'.format(LISTEN_PORT), new=0)

            except BaseException: # pylint: disable=broad-except
                logging.error(traceback.format_exc())

    def handle_params_panel(self, params):

        params = dict(params)
        for (k, v) in params.items():
            if self.context['backend'].params.get(k):
                self.context['backend'].params[k]['value'] = v
        logging.info(f"{self.context['backend'].params}")
        # ~ self.context['backend'].update_params(params)

    def render_params_panel(self):

        html_ = "<table>"
        html_ += f'<tr><th colspan="2"> params_panel </th></tr>'
        for k, v in self.context['backend'].params.items():
            if v['type'] == 'int':
                _type = f"""type="number" step="1" id="{k}" min="{v.get('min', 0)}" min="{v.get('max', 100)}" """
            elif v['type'] == 'float':
                _type = f"""type="number" step="0.1" id="{k}" min="{v.get('min', 0)}" min="{v.get('max', 1.)}" """
            else:
                _type = f'type="text" size=40'
            html_ += f"""<tr>
            <td title="{v['description']}"><label for=""{k}"">{k}:</label></td>
            <td><input {_type} id="{k}" value="{v['value']}" class="model_param" onchange="render_data_graph();"></input></td>
            </tr>"""

        html_ += '</table>'

        self.send_message_to_UI("params_panel", html_)

    def render_data_graph(self, title, data, start, stop):

        line_chart = pygal.XY(
            width=900,
            height=500,
            x_label_rotation=30,
            dots_size=0.5,
            stroke_style={'width': 1.},
            # ~ stroke=False,
            # ~ show_dots=False,
            # ~ show_legend=False, 
            human_readable=True, 
            legend_at_bottom=True,
            # ~ legend_at_bottom_columns=len(data),
            # ~ legend_box_size=40,
            truncate_legend=40,
        )

        line_chart.title = title

        for sample in data[start:stop+1]:
            _line = "1 {}".format(sample.get('name')), sample['spectra_lines'][0]
            line_chart.add(*_line)
            if sample['spectra_lines'][1]:
                _line = "2 " + sample.get('name'), sample['spectra_lines'][1]
                line_chart.add(*_line)

        graph_svg = line_chart.render(is_unicode=True)
        self.send_message_to_UI("data_graph", graph_svg)

        # ~ line_chart.render_to_file('samples.svg')   

    async def handle_message_from_UI(self, ws_socket, message):

        logging.debug(f"message({type(message)}):{message}")
        message_dict = json.loads(message)

        if message_dict.get("command") == "reset_model_params":

            self.context['backend'].reset_params()
            self.render_params_panel()

        elif message_dict.get("command") == "render_data_graph":

            params = message_dict.get("params", [])
            self.handle_params_panel(params)

            start = self.context['backend'].params.get('start', {}).get('value', 0)
            stop = self.context['backend'].params.get('stop', {}).get('value', 1)
            title = self.context['backend'].title
            data = self.context['backend'].run_model()

            self.render_data_graph(title, data, int(start), int(stop))

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

