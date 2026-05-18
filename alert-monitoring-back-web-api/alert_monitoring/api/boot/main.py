from dotenv import load_dotenv
load_dotenv()

import logging
import os
from pathlib import Path

from fwkpy_lib_fastapi import FastAPIBuilder
from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

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


def _run_migrations() -> None:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "alert_monitoring")
    user = os.getenv("DB_USER", "sa")
    password = os.getenv("DB_PASSWORD", "root")
    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE default_alert_catalog ADD COLUMN IF NOT EXISTS solution VARCHAR"
        ))


@app.on_event("startup")
async def log_env_loaded():
    if Path(".env").exists():
        logging.getLogger("uvicorn.error").info("Loading environment from '.env'")
    _run_migrations()