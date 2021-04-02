# coding: utf-8

# pylint: disable=missing-docstring

import sys
import logging
import asyncio

from alhazen.frontend import Frontend
from alhazen.backend import Backend
from alhazen.console import Console


LOG_LEVEL = "INFO"
LOG_LEVEL = "ERROR"

def start():

    common_context = {
        'frontend': Frontend(),
        'backend': Backend(),
        'console': Console(),
    }

    for o in common_context.values():
        o.context = common_context
        t_ = o.run()
        asyncio.ensure_future(t_)
        logging.info(f"o:{o}")

    return common_context

def load_config(pth):

    config = None
    with open(pth) as f:
        config = json.load(f)

    return config

def set_logging():

    logging.basicConfig(
        stream=sys.stdout,
        level=LOG_LEVEL,
        format="[%(asctime)s]%(levelname)s %(funcName)s() %(filename)s:%(lineno)d %(message)s")

def main():

    set_logging()
    load_config()
    start()
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
