"""Helpers de respuesta HTTP para los controladores REST.

Centralizan el patrón repetido de construir una ``JSONResponse`` 200 con el
cuerpo serializado mediante ``jsonable_encoder``. El comportamiento es idéntico
al código que sustituyen.
"""
from typing import Iterable, Type

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def ok_json(content) -> JSONResponse:
    """Devuelve una respuesta 200 con ``content`` serializado."""
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(content))


def ok_list(response_cls: Type, items: Iterable) -> JSONResponse:
    """Devuelve una respuesta 200 con la lista de ``items`` mapeada a ``response_cls``.

    Cada elemento se convierte con ``response_cls(**item.model_dump())``, igual
    que hacían los controladores manualmente.
    """
    return ok_json([response_cls(**item.model_dump()) for item in items])
