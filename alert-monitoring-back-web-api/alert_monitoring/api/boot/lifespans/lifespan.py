import logging
from pathlib import Path

from fwkpy_lib_fastapi.public.lifespan import Lifespan


class AlertMonitoringLifespan(Lifespan):

    async def startup_actions(self, app):
        if Path(".env").exists():
            logging.getLogger("uvicorn.error").info("Loading environment from '.env'")

    async def shutdown_actions(self, app):
        pass
