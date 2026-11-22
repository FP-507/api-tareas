"""Conexión a la base de datos SQLite."""

import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tareas.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def crear_tablas() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
