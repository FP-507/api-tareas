from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app


@pytest.fixture
def client():
    """Cada test usa una base de datos en memoria nueva."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def session_de_prueba():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_de_prueba
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def crear(client, **datos):
    datos.setdefault("titulo", "Estudiar SQL")
    r = client.post("/tareas", json=datos)
    assert r.status_code == 201, r.text
    return r.json()


def test_crear_y_leer(client):
    tarea = crear(client, titulo="Leer documentación", prioridad="alta")
    assert tarea["id"] == 1
    assert tarea["completada"] is False

    r = client.get(f"/tareas/{tarea['id']}")
    assert r.status_code == 200
    assert r.json()["titulo"] == "Leer documentación"


def test_titulo_vacio_es_rechazado(client):
    r = client.post("/tareas", json={"titulo": ""})
    assert r.status_code == 422


def test_tarea_inexistente_da_404(client):
    assert client.get("/tareas/999").status_code == 404
    assert client.patch("/tareas/999", json={"completada": True}).status_code == 404
    assert client.delete("/tareas/999").status_code == 404


def test_actualizar_solo_cambia_lo_enviado(client):
    tarea = crear(client, titulo="Original", descripcion="no cambia")
    r = client.patch(f"/tareas/{tarea['id']}", json={"completada": True})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["completada"] is True
    assert cuerpo["titulo"] == "Original"
    assert cuerpo["descripcion"] == "no cambia"


def test_borrar(client):
    tarea = crear(client)
    assert client.delete(f"/tareas/{tarea['id']}").status_code == 204
    assert client.get(f"/tareas/{tarea['id']}").status_code == 404


def test_filtros_y_busqueda(client):
    crear(client, titulo="Comprar café", prioridad="baja")
    crear(client, titulo="Preparar examen", prioridad="alta")
    t3 = crear(client, titulo="Repasar examen de SQL", prioridad="alta")
    client.patch(f"/tareas/{t3['id']}", json={"completada": True})

    altas = client.get("/tareas", params={"prioridad": "alta"}).json()
    assert [t["titulo"] for t in altas] == ["Preparar examen", "Repasar examen de SQL"]

    pendientes = client.get("/tareas", params={"completada": False}).json()
    assert len(pendientes) == 2

    examen = client.get("/tareas", params={"buscar": "EXAMEN"}).json()
    assert len(examen) == 2


def test_paginacion(client):
    for i in range(5):
        crear(client, titulo=f"Tarea {i}")
    pagina = client.get("/tareas", params={"offset": 2, "limite": 2}).json()
    assert [t["titulo"] for t in pagina] == ["Tarea 2", "Tarea 3"]


def test_resumen(client):
    ayer = (date.today() - timedelta(days=1)).isoformat()
    crear(client, titulo="Vencida", fecha_limite=ayer, prioridad="alta")
    hecha = crear(client, titulo="Hecha", fecha_limite=ayer)
    client.patch(f"/tareas/{hecha['id']}", json={"completada": True})
    crear(client, titulo="Normal", prioridad="baja")

    r = client.get("/tareas/resumen").json()
    assert r["total"] == 3
    assert r["completadas"] == 1
    assert r["pendientes"] == 2
    assert r["vencidas"] == 1
    assert r["por_prioridad"] == {"baja": 1, "media": 1, "alta": 1}
