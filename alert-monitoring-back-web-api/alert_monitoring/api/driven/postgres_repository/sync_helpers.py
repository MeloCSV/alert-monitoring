"""Helpers reutilizables para los adaptadores de persistencia (postgres).

Centralizan los dos patrones de escritura que se repetían, campo a campo, en
varios repositorios:

- ``reconcile_by_key``: sincroniza una tabla completa contra un lote entrante
  (inserta lo nuevo, actualiza lo existente y borra lo que ya no llega).
- ``upsert_preserving_display``: hace upsert de "alertas por defecto"
  preservando las ediciones manuales de los campos ``display_*``.

El comportamiento es idéntico al que tenían los repositorios; solo se elimina
la duplicación.
"""
from typing import Callable, Iterable, List, Type, TypeVar

TModel = TypeVar("TModel")
TItem = TypeVar("TItem")


def reconcile_by_key(
    session,
    model_cls: Type[TModel],
    items: Iterable[TItem],
    *,
    key_attr: str,
    apply_fn: Callable[[TModel, TItem], None],
) -> None:
    """Sincroniza ``model_cls`` con ``items`` usando ``key_attr`` como clave natural.

    - Inserta las filas cuyo ``key_attr`` no existe todavía.
    - Actualiza (vía ``apply_fn``) las que ya existen.
    - Borra las filas existentes cuya clave no está en el lote entrante.
    """
    existing = {
        getattr(row, key_attr): row
        for row in session.query(model_cls).all()
    }
    incoming_keys = {getattr(item, key_attr) for item in items}

    for item in items:
        row = existing.get(getattr(item, key_attr))
        if row is None:
            row = model_cls()
            session.add(row)
        apply_fn(row, item)

    for key, row in existing.items():
        if key not in incoming_keys:
            session.delete(row)

    session.commit()


def upsert_preserving_display(
    session,
    model_cls: Type[TModel],
    items: List[TItem],
    *,
    owned_fields: Callable[[TItem], dict],
) -> None:
    """Upsert por ``raw_name`` que preserva las ediciones manuales de ``display_*``.

    ``owned_fields`` devuelve el diccionario de campos "propiedad" del origen
    (Prometheus/Kibana) que siempre se sobrescriben. ``severity`` y
    ``notification_channel`` solo se actualizan si llegan con valor, y los
    campos ``display_*`` solo se rellenan si estaban a ``None``.
    """
    for item in items:
        existing = (
            session.query(model_cls)
            .filter(model_cls.raw_name == item.raw_name)
            .first()
        )
        owned = owned_fields(item)
        if existing is None:
            session.add(model_cls(
                raw_name=item.raw_name,
                display_name=item.display_name or item.raw_name,
                display_description=item.display_description,
                severity=item.severity,
                notification_channel=item.notification_channel,
                **owned,
            ))
        else:
            for attr, value in owned.items():
                setattr(existing, attr, value)
            if item.severity:
                existing.severity = item.severity
            if item.notification_channel:
                existing.notification_channel = item.notification_channel
            if existing.display_name is None:
                existing.display_name = item.display_name or item.raw_name
            if existing.display_description is None and item.display_description:
                existing.display_description = item.display_description
    session.commit()
