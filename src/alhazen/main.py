# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import sys
import logging
import asyncio
import json

from alhazen.frontend import Frontend
from alhazen.backend import Backend
from alhazen.console import Console


LOG_LEVEL = "INFO"
# ~ LOG_LEVEL = "ERROR"

def start(settings):

    common_context = {
        'frontend': Frontend(),
        'backend': Backend(),
        'console': Console(),
        'settings': settings,
    }

    for k_ in ('backend', 'frontend', 'console'):
        instance = common_context[k_]
        instance.context = common_context
        t_ = instance.run()
        asyncio.ensure_future(t_)
        # ~ logging.info("instance:%s", instance)


    return common_context

def load_settings(pth):

    settings = {}
    if pth:
        with open(pth) as f:
            settings = json.load(f)

    return settings

def set_logging(log_level):

    logging.basicConfig(
        stream=sys.stdout,
        level=log_level,
        format="[%(asctime)s]%(levelname)s %(funcName)s() %(filename)s:%(lineno)d %(message)s")

def main():

    set_logging(LOG_LEVEL)

    pth = ''
    if sys.argv[1:]:
        pth = sys.argv[1]

    settings = load_settings(pth)
    start(settings)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
