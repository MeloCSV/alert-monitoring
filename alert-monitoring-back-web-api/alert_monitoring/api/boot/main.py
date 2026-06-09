from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path

from fwkpy_lib_fastapi import FastAPIBuilder
from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware

set_i18n()
translations_path = Path(os.path.dirname(__file__))
load_translations(os.path.join(translations_path, 'resources/i18n'))

Injector.preload_all_classes()

app = FastAPIBuilder()

add_session_middleware(app)