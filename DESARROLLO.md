# Notas de desarrollo · API de Tareas

Guía para retomar el proyecto: cómo está armado, por qué y cómo cambiarlo.

## Puesta en marcha

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://127.0.0.1:8000/docs
pytest -q
```

Variable de entorno opcional: `DATABASE_URL` (por defecto `sqlite:///./tareas.db`). En Docker apunta a `/data/tareas.db`, que es un volumen.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `app/database.py` | Crea el `engine` a partir de `DATABASE_URL`; `crear_tablas()` y `get_session()` (dependencia de FastAPI que abre y cierra una sesión por petición) |
| `app/models.py` | `Tarea` (tabla) y los esquemas `TareaCrear`, `TareaActualizar`, `TareaLeer`, `Resumen`; enum `Prioridad` |
| `app/main.py` | La app, el `lifespan` que crea las tablas al arrancar, y las rutas |
| `tests/test_api.py` | 8 tests con `TestClient` y SQLite en memoria |

## Decisiones

- **Un modelo de tabla y varios esquemas.** `TareaBase` tiene los campos editables; `Tarea` agrega `id`, `completada` y `creada_en`; `TareaCrear` no deja enviar `id` ni `completada`; `TareaActualizar` tiene todo opcional. Así la API no acepta campos que no debería.
- **`PATCH` con `exclude_unset=True`:** solo se cambian los campos enviados; enviar `null` explícitamente sí borra el valor.
- **Orden de las rutas:** `/tareas/resumen` va antes de `/tareas/{tarea_id}` (comentado en el código).
- **Estadísticas en SQL** (`COUNT`, `GROUP BY`) en lugar de traer todas las filas a Python. `por_prioridad` empieza con todas las prioridades en 0, para que siempre aparezcan las tres.
- **Paginación** con `offset` y `limite` (máximo 100) validados por `Query`.
- **Búsqueda** con `icontains` (sin distinguir mayúsculas).
- **Fechas en UTC** con zona horaria (`datetime.now(timezone.utc)`).
- **`check_same_thread=False`:** FastAPI puede atender una petición en un hilo distinto del que creó la conexión SQLite.

## Tests

`tests/test_api.py` sobrescribe la dependencia `get_session` (`app.dependency_overrides`) con una base SQLite en memoria y `StaticPool`, de modo que todas las conexiones vean la misma base y cada test empiece limpio. Cubre crear y leer, validación (422), 404, `PATCH` parcial, borrado, filtros y búsqueda, paginación y el resumen. La CI los corre en cada push.

## Cómo extenderlo

- **Nuevo campo:** agregarlo a `TareaBase` (y como opcional a `TareaActualizar`). SQLModel no migra tablas existentes: en desarrollo basta con borrar `tareas.db`; en producción habría que sumar Alembic.
- **Nuevo filtro:** agregar el parámetro a `listar_tareas` y un `where` condicional.
- **Usuarios y autenticación:** ver el proyecto `agenda-clinica`, que ya resuelve JWT y roles con la misma base técnica.
- **Otra base de datos:** cambiar `DATABASE_URL` (por ejemplo, PostgreSQL) y quitar `check_same_thread`, que solo aplica a SQLite.

## Pendientes

- Migraciones con Alembic.
- Ordenar el listado por fecha límite o prioridad (hoy ordena por `id`).
- Etiquetas o proyectos para agrupar tareas.
