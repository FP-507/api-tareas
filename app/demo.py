"""Datos de ejemplo para la demo pública.

Solo se cargan si la variable de entorno SEMBRAR_DEMO vale "1" y la tabla está vacía.
En Render (plan gratuito) el disco se borra cada vez que el servicio se reinicia, así que
la demo vuelve siempre a este estado inicial. Los tests no la activan.
"""

import os
from datetime import date, timedelta

from sqlmodel import Session, func, select

from .models import Prioridad, Tarea


def ejemplos(hoy: date) -> list[Tarea]:
    return [
        Tarea(titulo="Preparar la presentación del proyecto", prioridad=Prioridad.alta,
              fecha_limite=hoy + timedelta(days=2)),
        Tarea(titulo="Revisar el informe de ventas", descripcion="Comparar con el trimestre anterior",
              prioridad=Prioridad.media, fecha_limite=hoy - timedelta(days=1)),
        Tarea(titulo="Actualizar dependencias", prioridad=Prioridad.baja, completada=True),
        Tarea(titulo="Escribir tests del módulo de pagos", prioridad=Prioridad.alta,
              fecha_limite=hoy + timedelta(days=5)),
        Tarea(titulo="Responder correos pendientes", prioridad=Prioridad.media, completada=True),
    ]


def sembrar_si_corresponde(session: Session) -> int:
    """Inserta las tareas de ejemplo y devuelve cuántas creó (0 si no correspondía)."""
    if os.getenv("SEMBRAR_DEMO") != "1":
        return 0
    if session.exec(select(func.count()).select_from(Tarea)).one() > 0:
        return 0
    tareas = ejemplos(date.today())
    session.add_all(tareas)
    session.commit()
    return len(tareas)
