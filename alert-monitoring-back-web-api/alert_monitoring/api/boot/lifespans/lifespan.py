import logging
from pathlib import Path

from fwkpy_lib_fastapi.public.lifespan import Lifespan


class AlertMonitoringLifespan(Lifespan):

    async def on_startup(self, app):
        if Path(".env").exists():
            logging.getLogger("uvicorn.error").info("Loading environment from '.env'")

    async def on_shutdown(self, app):
        pass
