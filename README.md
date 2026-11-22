# API de Tareas

API REST para gestionar tareas, hecha con **FastAPI** y **SQLite** (vía SQLModel). Incluye filtros, búsqueda, paginación, un endpoint de estadísticas, tests automáticos y un contenedor Docker.

![tests](https://github.com/FP-507/api-tareas/actions/workflows/tests.yml/badge.svg)

## Qué aprendí con este proyecto

- Diseñar endpoints REST con los códigos HTTP correctos (201, 204, 404, 422).
- Separar el modelo de la tabla de los esquemas de entrada y salida.
- Consultas SQL con filtros, `GROUP BY` y conteos desde un ORM.
- Inyección de dependencias para cambiar la base de datos en los tests.
- Integración continua con GitHub Actions y empaquetado con Docker.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/tareas` | Crea una tarea |
| `GET` | `/tareas` | Lista tareas. Filtros: `completada`, `prioridad`, `buscar`, `offset`, `limite` |
| `GET` | `/tareas/{id}` | Obtiene una tarea |
| `PATCH` | `/tareas/{id}` | Actualiza solo los campos enviados |
| `DELETE` | `/tareas/{id}` | Borra una tarea |
| `GET` | `/tareas/resumen` | Totales, pendientes, vencidas y conteo por prioridad |

## Cómo ejecutarlo

```bash
python -m venv .venv
.venv\Scripts\activate        # en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000/docs> para probar la API desde el navegador.

### Con Docker

```bash
docker build -t api-tareas .
docker run -p 8000:8000 -v tareas-data:/data api-tareas
```

## Ejemplo

```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Estudiar SQL", "prioridad": "alta", "fecha_limite": "2026-12-01"}'
```

```json
{
  "titulo": "Estudiar SQL",
  "descripcion": null,
  "prioridad": "alta",
  "fecha_limite": "2026-12-01",
  "id": 1,
  "completada": false,
  "creada_en": "2026-11-22T17:00:00Z"
}
```

## Tests

```bash
pytest -v
```

Cada test usa una base de datos SQLite en memoria, así que no tocan tus datos.

## Estructura

```
app/
  main.py       # rutas de la API
  models.py     # tabla y esquemas
  database.py   # conexión a SQLite
tests/
  test_api.py
```
