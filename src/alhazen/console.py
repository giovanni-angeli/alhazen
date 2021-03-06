# coding: utf-8

# pylint: disable=missing-docstring

import os
import logging
import traceback
import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

HISTORY_PATH = '.alhazen_history'

open(HISTORY_PATH, 'a').close()

class Console:

    async def run(self):
        
        # TODO: implement console
        logging.warning("console is disabled (To Be Implemented)")
        # ~ return

        session = PromptSession(history=FileHistory(HISTORY_PATH))
        while True:
            with patch_stdout():
                input = await session.prompt_async('>>> ', auto_suggest=AutoSuggestFromHistory())
                try:
                    if input.strip():
                        answer = eval(input)
                        print('<<< {}'.format(answer))
                except SyntaxError:
                    exec(input)
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break
                except Exception as e:
                    # ~ logging.warning(traceback.format_exc())
                    logging.error(f"{e}")
