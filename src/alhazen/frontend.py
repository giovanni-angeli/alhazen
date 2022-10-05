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

from alhazen.backend import (
    STRUCTURE_FILES_PATH,
    MEASURE_FILES_PATH,
    DATA_TEMPLATES_PATH,
    DATA_PATH)

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

        ctx = {
            'page_name': 'Alhazen conf page',
            'page_links': [('/', 'graph page'), ],
            'result_title': result_title,
            'results': results,
            'errors': errors,
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

        structure_file_list = [''] + os.listdir(STRUCTURE_FILES_PATH)
        measure_file_list = [''] + os.listdir(MEASURE_FILES_PATH)

        ctx = {
            'page_name': 'Alhazen graph page',
            'page_links': [('/setup', 'conf page'), ],
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
                urls = [
                    f'http://127.0.0.1:{LISTEN_PORT}/setup',
                    f'http://127.0.0.1:{LISTEN_PORT}']
                for url in urls:
                    try:
                        webbrowser.get(BROWSER).open(url, new=0)
                    except BaseException:
                        webbrowser.open(url, new=0)

        except BaseException:  # pylint: disable=broad-except
            logging.error(traceback.format_exc())

    async def send_message_to_UI(self, element_id, payload, target='innerHTML', class_name=None, ws_socket=None):

        msg = {
            "element_id": element_id,
            'target': target,
            'payload': payload,
            'class_name': class_name}

        msg = json.dumps(msg)

        if ws_socket:
            await ws_socket.write_message(msg)

        else:  # broadcast
            for ws_ch in self.web_socket_channels:
                await ws_ch.write_message(msg)

    async def refresh_data_graph(self, params, ws_socket):

        await self.send_message_to_UI("status_display", 'recalculating model, please wait...', ws_socket=ws_socket)

        self.backend.load_structure()
        self.backend.load_measure()

        data, message = self.backend.refresh_model_data(params)

        if data:
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

            # ~ line_chart.title = f"params:{params}"
            line_chart.title = ""
            line_chart.x_labels = [i * 10 for i in range(0, int(len(data[0]) / 10))]

            for line in data:
                label, serie = line
                line_chart.add(label, serie)

            STATIC_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'static')
            line_chart.render_to_file(STATIC_PATH + '/temp_chart.svg')
            await self.send_message_to_UI("pygal_data_container",
                                          payload='/static/temp_chart.svg', target='data', ws_socket=ws_socket)

            await self.send_message_to_UI("pygal_description_container", message, ws_socket=ws_socket)

        _msg = f"structure_file:{self.backend.structure_file}"
        _msg += f", measure_file:{self.backend.measure_file}"
        await self.send_message_to_UI("status_display", f"done.<br/>{_msg}", ws_socket=ws_socket)

    async def refresh_file_lists(self, ws_socket):

        structure_file_list = os.listdir(STRUCTURE_FILES_PATH)
        measure_file_list = os.listdir(MEASURE_FILES_PATH)
        structure_file_list.sort()
        measure_file_list.sort()
        for name, list_, element_id in (
                ('structure', structure_file_list, 'structure_file_list'),
                ('measure', measure_file_list, 'measure_file_list')):

            html_ = f"<h3>{name} files:</h3>"
            for n, f in enumerate(list_):
                col = "#F7FAF7" if n % 2 else "#EEEEEE"
                html_ += f"""
<div class="row" style="background-color:{col};">
<span class="col-7">{str(f)}</span>\n
<span class="small_btn col-1" onclick="on_template_clicked('edit',   '{str(name)}', '{str(f)}')">edit  </span>
<span class="small_btn col-1" onclick="on_template_clicked('delete', '{str(name)}', '{str(f)}')">delete</span>
<span class="small_btn col-1" onclick="on_template_clicked('clone',  '{str(name)}', '{str(f)}')">clone </span>
</div>
"""

            await self.send_message_to_UI(element_id, html_, ws_socket=ws_socket)

    async def handle_message_from_UI(self, ws_socket, message):

        logging.debug(f"message({type(message)}):{message}")
        message_dict = json.loads(message)
        try:

            if message_dict.get("command"):
                command = "_cmd_" + message_dict["command"]
                params = message_dict.get("params", {})
                await getattr(self, command)(params, ws_socket)

            else:
                answer = f"received:{message}"
                innerHTML = "ws_index:{} [{}] {} -> {}".format(
                    self.web_socket_channels.index(ws_socket), time.asctime(), message, answer)
                await self.send_message_to_UI("status_display", innerHTML, ws_socket=ws_socket)
                logging.warning(f"innerHTML:{innerHTML}")

        except Exception as e:
            logging.warning(traceback.format_exc())
            await self.send_message_to_UI("error_display", f"Exception:{e}", ws_socket=ws_socket)

    async def _cmd_refresh_file_lists(self, params, ws_socket):  # pylint: disable=unused-private-member, unused-argument

        await self.refresh_file_lists(ws_socket)

    async def _cmd_on_template_clicked(self, params, ws_socket):  # pylint: disable=unused-private-member

        _action = params.get('action')
        _type = params.get('type')
        _file_name = params.get('file_name')
        _file_content = params.get('file_content')

        logging.debug(f"params:{params}"[:200])

        if _action and _type and _file_name:
            if _action == 'delete':
                _pth = STRUCTURE_FILES_PATH if _type == 'structure' else MEASURE_FILES_PATH
                r = os.remove(os.path.join(_pth, _file_name))
                logging.warning(f"r:{r}")

            elif _action == 'edit':
                if _type == 'structure':
                    with open(os.path.join(STRUCTURE_FILES_PATH, _file_name), encoding='utf-8') as f:
                        _content = f.read()
                        _content = json.dumps(json.loads(_content), indent=2)
                        # ~ _content = "<br/>".join(_content.split('\n'))
                else:
                    with open(os.path.join(MEASURE_FILES_PATH, _file_name), encoding='utf-8') as f:
                        _content = f.read()
                        # ~ _content = "<br/>".join(_content.split('\n'))

                await self.send_message_to_UI("view_file_name", _file_name, class_name="view_file_container", ws_socket=ws_socket)
                await self.send_message_to_UI("view_file_type", _type, ws_socket=ws_socket)
                await self.send_message_to_UI("view_file_content", _content, ws_socket=ws_socket)

            elif _action == 'clone':
                _pth = STRUCTURE_FILES_PATH if _type == 'structure' else MEASURE_FILES_PATH
                original = os.path.join(_pth, _file_name)
                target = '.cpy'.join(os.path.splitext(original))

                shutil.copyfile(original, target)

            await self.refresh_file_lists(ws_socket)

    async def _cmd_structure_selected(self, params, ws_socket):  # pylint: disable=unused-private-member, unused-argument
        _name = params
        self.backend.load_structure(_name)

    async def _cmd_measure_selected(self, params, ws_socket):  # pylint: disable=unused-private-member, unused-argument

        _name = params
        self.backend.load_measure(_name)

    async def _cmd_install_templates(self, params, ws_socket):  # pylint: disable=unused-private-member, unused-argument

        shutil.copytree(DATA_TEMPLATES_PATH, DATA_PATH, dirs_exist_ok=True)

        logging.info(f"structure_files:{os.listdir(STRUCTURE_FILES_PATH)}")
        logging.info(f"measure_files:{os.listdir(MEASURE_FILES_PATH)}")

        await self.refresh_file_lists(ws_socket)

    async def _cmd_refresh_data_graph(self, params, ws_socket):  # pylint: disable=unused-private-member

        logging.debug(f"params:{json.dumps(params, indent=2)}")
        await self.refresh_data_graph(params, ws_socket)

    async def _cmd_save_template(self, params, ws_socket):  # pylint: disable=unused-private-member

        _type = params.get('type')
        _file_name = params.get('file_name')
        _file_content = params.get('file_content')
        logging.debug(f"params:{params}"[:200])
        _pth = STRUCTURE_FILES_PATH if _type == 'structure' else MEASURE_FILES_PATH
        if _type == 'structure':
            _file_content = json.dumps(json.loads(_file_content), indent=2)
        else:
            pass

        with open(os.path.join(_pth, _file_name), 'w', encoding='utf-8') as f:
            f.write(_file_content)

        await self.refresh_file_lists(ws_socket)
        await self.send_message_to_UI("status_display", f"file {_file_name} saved.", ws_socket=ws_socket)
