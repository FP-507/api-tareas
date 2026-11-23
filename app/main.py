"""API REST para gestionar tareas.

Ejecutar:  uvicorn app.main:app --reload
Documentación interactiva:  http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlmodel import Session, col, func, select

from .database import crear_tablas, engine, get_session
from .demo import sembrar_si_corresponde
from .models import Prioridad, Resumen, Tarea, TareaActualizar, TareaCrear, TareaLeer


@asynccontextmanager
async def lifespan(_: FastAPI):
    crear_tablas()
    with Session(engine) as session:
        sembrar_si_corresponde(session)
    yield


app = FastAPI(
    title="API de Tareas",
    description="CRUD de tareas con filtros, búsqueda y estadísticas.",
    version="1.0.0",
    lifespan=lifespan,
)

SessionDep = Annotated[Session, Depends(get_session)]


def obtener_tarea(tarea_id: int, session: Session) -> Tarea:
    tarea = session.get(Tarea, tarea_id)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"La tarea {tarea_id} no existe")
    return tarea


@app.get("/", tags=["estado"])
def raiz() -> dict[str, str]:
    return {"mensaje": "API de Tareas funcionando", "docs": "/docs"}


@app.post("/tareas", response_model=TareaLeer, status_code=status.HTTP_201_CREATED, tags=["tareas"])
def crear_tarea(datos: TareaCrear, session: SessionDep) -> Tarea:
    tarea = Tarea.model_validate(datos)
    session.add(tarea)
    session.commit()
    session.refresh(tarea)
    return tarea


@app.get("/tareas", response_model=list[TareaLeer], tags=["tareas"])
def listar_tareas(
    session: SessionDep,
    completada: bool | None = None,
    prioridad: Prioridad | None = None,
    buscar: Annotated[str | None, Query(description="Texto a buscar en el título")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Tarea]:
    consulta = select(Tarea)
    if completada is not None:
        consulta = consulta.where(Tarea.completada == completada)
    if prioridad is not None:
        consulta = consulta.where(Tarea.prioridad == prioridad)
    if buscar:
        consulta = consulta.where(col(Tarea.titulo).icontains(buscar))
    consulta = consulta.order_by(col(Tarea.id)).offset(offset).limit(limite)
    return list(session.exec(consulta).all())


# IMPORTANTE: esta ruta debe declararse antes de /tareas/{tarea_id}; si no, FastAPI
# intentaría interpretar "resumen" como un id y respondería 422.
@app.get("/tareas/resumen", response_model=Resumen, tags=["estadísticas"])
def resumen(session: SessionDep) -> Resumen:
    """Cuenta en la base (no en Python) totales, completadas, vencidas y tareas por prioridad."""
    total = session.exec(select(func.count()).select_from(Tarea)).one()
    completadas = session.exec(
        select(func.count()).select_from(Tarea).where(Tarea.completada == True)  # noqa: E712
    ).one()
    vencidas = session.exec(
        select(func.count())
        .select_from(Tarea)
        .where(Tarea.completada == False, col(Tarea.fecha_limite) < date.today())  # noqa: E712
    ).one()
    filas = session.exec(select(Tarea.prioridad, func.count()).group_by(Tarea.prioridad)).all()
    por_prioridad = {p.value: 0 for p in Prioridad}
    por_prioridad.update({p.value if isinstance(p, Prioridad) else p: n for p, n in filas})
    return Resumen(
        total=total,
        completadas=completadas,
        pendientes=total - completadas,
        vencidas=vencidas,
        por_prioridad=por_prioridad,
    )


@app.get("/tareas/{tarea_id}", response_model=TareaLeer, tags=["tareas"])
def leer_tarea(tarea_id: int, session: SessionDep) -> Tarea:
    return obtener_tarea(tarea_id, session)


@app.patch("/tareas/{tarea_id}", response_model=TareaLeer, tags=["tareas"])
def actualizar_tarea(tarea_id: int, cambios: TareaActualizar, session: SessionDep) -> Tarea:
    tarea = obtener_tarea(tarea_id, session)
    tarea.sqlmodel_update(cambios.model_dump(exclude_unset=True))
    session.add(tarea)
    session.commit()
    session.refresh(tarea)
    return tarea


@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tareas"])
def borrar_tarea(tarea_id: int, session: SessionDep) -> None:
    tarea = obtener_tarea(tarea_id, session)
    session.delete(tarea)
    session.commit()
