from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path

from fwkpy_lib_fastapi import FastAPIBuilder
from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware

from fastapi.middleware.cors import CORSMiddleware


set_i18n()
translations_path = Path(os.path.dirname(__file__))
load_translations(os.path.join(translations_path, 'resources/i18n'))

Injector.preload_all_classes()

app = FastAPIBuilder()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

add_session_middleware(app)