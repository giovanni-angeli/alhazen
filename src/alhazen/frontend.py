# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=consider-using-f-string
# pylint: disable=broad-except

import os
import time
import asyncio
import logging
import traceback
import json
import webbrowser
import shutil

import tornado.web            # pylint: disable=import-error
import tornado.httpserver     # pylint: disable=import-error
import tornado.ioloop         # pylint: disable=import-error
import tornado.websocket      # pylint: disable=import-error
import tornado.options        # pylint: disable=import-error

import pygal  # pylint: disable=import-error

from alhazen.backend import (STRUCTURE_FILES_PATH, MEASURE_FILES_PATH)

WS_URI = r'/websocket'
LISTEN_PORT = 8000
LISTEN_ADDRESS = '127.0.0.1'
# ~ LISTEN_ADDRESS = '*'

# ~ BROWSER = "firefox"
# ~ BROWSER = "chromium"
BROWSER = None


class BaseRequestHandler(tornado.web.RequestHandler):  # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):

        logging.debug(f"args:{args}, kwargs:{kwargs}")
        self.parent = kwargs.pop('parent')
        super().__init__(*args, **kwargs)

    def data_received(self, *args, **kwargs):

        logging.warning(f"args:{args}, kwargs:{kwargs}")


class Setup(BaseRequestHandler):  # pylint: disable=too-few-public-methods

    @staticmethod
    def __get_context(result_title, results, errors):

        structure_file_list = os.listdir(STRUCTURE_FILES_PATH)
        measure_file_list = os.listdir(MEASURE_FILES_PATH)

        ctx = {
            'page_name': 'Alhazen conf page',
            'page_links': [('/', 'graph page'),],
            'ws_connection': True,
            'result_title': result_title,
            'results': results,
            'errors': errors,
            'structure_file_list': structure_file_list,
            'measure_file_list': measure_file_list,
        }

        return ctx

    def get(self):

        ctx = self.__get_context(result_title='', results=[], errors=[])
        return self.render("setup.html", **ctx)

    def post(self):

        logging.warning(f"self.request:{self.request}")

        results = []
        errors = []
        for key, path in (
                ('structure_file', STRUCTURE_FILES_PATH),
                ('measure_file', MEASURE_FILES_PATH)):

            for _file in self.request.files.get(key, []):
                original_fname = _file['filename']
                try:
                    with open(os.path.join(path, original_fname), 'wb') as output_file:
                        output_file.write(_file['body'])
                    results.append(original_fname)
                except Exception as e:
                    errors.append(e)

        ctx = self.__get_context(result_title="uploaded files:", results=results, errors=errors)
        return self.render("setup.html", **ctx)


class Index(BaseRequestHandler):  # pylint: disable=too-few-public-methods

    def get(self):

        structure_file_list = os.listdir(STRUCTURE_FILES_PATH)
        measure_file_list = os.listdir(MEASURE_FILES_PATH)

        ctx = {
            'page_name': 'Alhazen graph page',
            'page_links': [('/setup', 'conf page'),],
            'ws_connection': True,
            'structure_file': self.parent.backend.structure_file,
            'measure_file': self.parent.backend.measure_file,
            'structure_file_list': structure_file_list,
            'measure_file_list': measure_file_list,
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

        logging.debug(f"args:{args}, kwargs:{kwargs}")
        super().open(args, kwargs)

    def on_message(self, message):

        logging.debug(f"message:{message}")

        if self.parent:
            t_ = self.parent.handle_message_from_UI(self, message)
            asyncio.ensure_future(t_)

    def on_close(self):

        if self.parent:
            self.parent.web_socket_channels.remove(self)
            logging.info(f"n. of active web_socket_channels:{len(self.parent.web_socket_channels)}")

    def data_received(self, *args, **kwargs):

        logging.warning(f"args:{args}, kwargs:{kwargs}")


class Frontend(tornado.web.Application):

    def __init__(self, settings, backend):

        self.backend = backend

        self.web_socket_channels = []

        url_map = [
            (r"/", Index, {'parent': self}),
            (r"/setup", Setup, {'parent': self}),
            (WS_URI, WebsockHandler, {'parent': self}),
        ]
        super().__init__(url_map, **settings)

    async def run(self):

        logging.info("starting tornado webserver on http://{}:{} ...".format(LISTEN_ADDRESS, LISTEN_PORT))
        self.listen(LISTEN_PORT, LISTEN_ADDRESS)

        try:

            if BROWSER is not None:
                logging.warning("starting browser ...")
                try:
                    webbrowser.get(BROWSER).open('http://127.0.0.1:{}'.format(LISTEN_PORT), new=0)
                except BaseException:
                    webbrowser.open('http://127.0.0.1:{}'.format(LISTEN_PORT), new=0)

        except BaseException:  # pylint: disable=broad-except
            logging.error(traceback.format_exc())


    async def refresh_data_graph(self, ws_socket, params):

        data = self.backend.load_structure()
        data = self.backend.load_measure()
        data = self.backend.refresh_model_data(params)

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

        line_chart.title = ''
        line_chart.x_labels = [i * 10 for i in range(0, int(len(data[0]) / 10))]

        for line in data:
            label, serie = line
            line_chart.add(label, serie)

        # ~ graph_svg = line_chart.render(is_unicode=True)
        # ~ await self.send_message_to_UI("pygal_data_container", innerHTML=None, ws_client=ws_socket, data=graph_svg)

        STATIC_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'static')
        line_chart.render_to_file(STATIC_PATH + '/temp_chart.svg')
        await self.send_message_to_UI("pygal_data_container", payload='/static/temp_chart.svg', ws_client=ws_socket, target='data')

        await self.send_message_to_UI("pygal_description_container", '', ws_socket)

    async def handle_message_from_UI(self, ws_socket, message):

        logging.debug(f"message({type(message)}):{message}")
        message_dict = json.loads(message)
        try:

            if message_dict.get("command") == "install_templates":

                self.backend.install_templates()

            elif message_dict.get("command") == "on_template_clicked":

                _action = message_dict.get("params", {}).get('action')
                _type = message_dict.get("params", {}).get('type')
                _file_name = message_dict.get("params", {}).get('file_name')

                logging.warning(f"_type:{_type}, _file_name:{_file_name}")

                if _action and _type and _file_name:
                    if _action == 'delete':
                        _pth = STRUCTURE_FILES_PATH if _type == 'structure' else MEASURE_FILES_PATH
                        r = os.remove(os.path.join(_pth, _file_name)) 
                        logging.warning(f"r:{r}")
                    elif _action == 'edit':
                        pass
                    elif _action == 'clone':
                        _pth = STRUCTURE_FILES_PATH if _type == 'structure' else MEASURE_FILES_PATH
                        original = os.path.join(_pth, _file_name)
                        target = '.cpy'.join(os.path.splitext(original))

                        shutil.copyfile(original, target)



            elif message_dict.get("command") == "structure_selected":

                _name = message_dict.get("params")
                self.backend.load_structure(_name)

            elif message_dict.get("command") == "measure_selected":

                _name = message_dict.get("params")
                self.backend.load_measure(_name)

            elif message_dict.get("command") == "refresh_data_graph":

                await self.send_message_to_UI("status_display", 'recalculating model, please wait...', ws_socket)
                await self.refresh_data_graph(ws_socket, params=message_dict.get("params", {}))
                _msg = f"structure_file:{self.backend.structure_file}, measure_file:{self.backend.measure_file}"
                await self.send_message_to_UI("status_display", f"done.<br/>{_msg}", ws_socket)

            else:
                answer = f"received:{message}"
                innerHTML = "ws_index:{} [{}] {} -> {}".format(
                    self.web_socket_channels.index(ws_socket), time.asctime(), message, answer)
                await self.send_message_to_UI("status_display", innerHTML, ws_socket)
                logging.warning(f"innerHTML:{innerHTML}")

            # ~ await self.send_message_to_UI("error_display", "-", ws_socket)

        except Exception as e:
            logging.warning(traceback.format_exc())
            await self.send_message_to_UI("error_display", f"Exception:{e}", ws_socket)

    async def send_message_to_UI(self, element_id, payload, ws_client=None, target='innerHTML'):

        msg = {"element_id": element_id, 'target': target, 'payload': payload}
        msg = json.dumps(msg)

        if ws_client:
            await ws_client.write_message(msg)
            # ~ t_ = ws_client.write_message(msg)
            # ~ asyncio.ensure_future(t_)

        else:  # broadcast
            for ws_ch in self.web_socket_channels:
                await ws_ch.write_message(msg)
                # ~ t_ = ws_ch.write_message(msg)
                # ~ asyncio.ensure_future(t_)
