"""Modelos de datos: la tabla de tareas y los esquemas de entrada/salida."""

from datetime import date, datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class Prioridad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"


class TareaBase(SQLModel):
    titulo: str = Field(min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, max_length=1000)
    prioridad: Prioridad = Prioridad.media
    fecha_limite: date | None = None


class Tarea(TareaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    completada: bool = False
    creada_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TareaCrear(TareaBase):
    pass


class TareaActualizar(SQLModel):
    """Todos los campos son opcionales: solo se cambia lo que se envía."""

    titulo: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, max_length=1000)
    prioridad: Prioridad | None = None
    fecha_limite: date | None = None
    completada: bool | None = None


class TareaLeer(TareaBase):
    id: int
    completada: bool
    creada_en: datetime


class Resumen(SQLModel):
    total: int
    completadas: int
    pendientes: int
    vencidas: int
    por_prioridad: dict[str, int]
