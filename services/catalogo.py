from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Type, Any
from config import CADENAS_NORM
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))



def listar_catalogo(
        db: Session,
        modelo,
        filtros: dict = None,
        campos_busqueda: list = None,
        q: str = None,
        page: int = 1,
        page_size: int = 50,
):
    """
    Servicio genérico para listar cualquier catálogo con:
    - Filtros exactos por campo
    - Búsqueda libre (q) sobre campos_busqueda
    - Paginación
    """
    query = db.query(modelo)

    # Filtros exactos
    if filtros:
        for campo, valor in filtros.items():
            if valor is not None and valor != "":
                col = getattr(modelo, campo, None)
                if col is not None:
                    query = query.filter(col.ilike(f"%{valor}%"))

    # Búsqueda libre sobre múltiples columnas
    if q and campos_busqueda:
        condiciones = []
        for campo in campos_busqueda:
            col = getattr(modelo, campo, None)
            if col is not None:
                condiciones.append(col.ilike(f"%{q}%"))
        if condiciones:
            query = query.filter(or_(*condiciones))

    total = query.count()
    offset = (page - 1) * page_size
    registros = query.order_by(modelo.id.desc()).offset(offset).limit(page_size).all()

    return {
        "registros": registros,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),  # ceil division
    }


def obtener_detalle(db: Session, modelo, registro_id: int):
    return db.query(modelo).filter(modelo.id == registro_id).first()

def sql_normalizar_cadena(col: str = "pv.cadena_str") -> str:
    """
    Genera un CASE SQL para normalizar nombres de cadenas.
    col: expresión SQL que contiene el nombre de la cadena
    """
    cases = "\n".join([
        f"    WHEN UPPER(TRIM({col})) = '{k}' THEN '{v}'"
        for k, v in CADENAS_NORM.items()
    ])
    return f"""
        CASE
{cases}
            WHEN {col} IS NULL
              OR TRIM({col}) = ''
              OR UPPER(TRIM({col})) = 'NAN' THEN 'Sin cadena'
            ELSE TRIM({col})
        END
    """