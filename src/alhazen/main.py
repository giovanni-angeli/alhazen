# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import os
import sys
import logging
import asyncio
import json
import time

from alhazen.frontend import Frontend
from alhazen.backend import Backend


LOG_LEVEL = "DEBUG"
# ~ LOG_LEVEL = "INFO"
# ~ LOG_LEVEL = "WARNING"
# ~ LOG_LEVEL = "ERROR"

HERE = os.path.dirname(os.path.abspath(__file__))

TORNADO_APPLICATION_OPTIONS = dict(
    debug=True,
    autoreload=True,
    # ~ debug=False,
    # ~ autoreload=False,
    template_path=os.path.join(HERE, "..", "templates"),
    static_path=os.path.join(HERE, "..", "static"),
    compiled_template_cache=False)


def start(settings):

    # augh: normalmente settings e` vuoto (vedi commento in main)
    backend = Backend(settings)
    # questo inizializza il frontend dicendogli chi e` il suo backend
    frontend = Frontend(TORNADO_APPLICATION_OPTIONS, backend)

    for instance in (backend, frontend):
        t_ = instance.run()
        asyncio.ensure_future(t_)
        logging.debug(f"instance:{instance}")

def load_settings(pth):

    settings = {}
    if pth:
        with open(pth, encoding="UTF-8") as f:
            settings = json.load(f)

    logging.debug(f"settings:{settings}")

    return settings

def set_logging(log_level):

    logging.basicConfig(
        stream=sys.stdout,
        level=log_level,
        format="[%(asctime)s]%(levelname)s %(funcName)s() %(filename)s:%(lineno)d %(message)s")

def main():

    set_logging(LOG_LEVEL)

    # da qui ...
    pth = ''
    if sys.argv[1:]:
        pth = sys.argv[1]

    logging.warning(f"time:{time.asctime()} starting application. settings pth:'{pth}'.")

    settings = load_settings(pth)
    # ... a qui serve pr caricare eventuali "settings" passati come
    # argomento. Di fatto, non utilizzato.
    start(settings)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
