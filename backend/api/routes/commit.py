from fastapi import APIRouter, Body, HTTPException

router = APIRouter()


def commit_to_postgis(rows: list[dict]) -> int:
    """TODO(cliente): escribir a su tabla PostgreSQL/PostGIS.

    Cuando el cliente entregue el esquema/credenciales:
      1. Leer DSN de env (p.ej. POSTGRES_DSN).
      2. Por cada row, INSERT en su tabla con:
         x, y, the_geom = ST_SetSRID(ST_MakePoint(x, y), 4326),
         fecha, zt, adreca, foto, idclient, is_unique_customer.
      3. Devolver cantidad de filas insertadas.
    Se deja como stub a propósito: la lógica de negocio la define el cliente.
    """
    raise NotImplementedError


@router.post("/commit")
def commit(payload: dict = Body(...)):
    raise HTTPException(status_code=501,
                        detail="commit a PostGIS no configurado (ver commit_to_postgis)")
