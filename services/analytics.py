import pandas as pd
import numpy as np

def procesar_reporte_gerencial(data_list, fecha_inicio=None, fecha_fin=None, agrupar_por="pdv"):
    """
    Procesa los KPIs de forma reactiva a los filtros.
    Retorna un diccionario con 'filas' para la tabla y 'totales' para las tarjetas.
    """
    # 1. Validación de entrada
    if not data_list:
        return {
            "filas": [],
            "totales": {"visitas": 0, "cumplimiento": 0, "agotados": 0}
        }

    df = pd.DataFrame(data_list)

    # 2. Limpieza y Filtro de Fechas (Crucial para que los totales cambien)
    col_fecha = next((c for c in ['fecha', 'created_at', 'fecha_registro'] if c in df.columns), None)
    if col_fecha:
        df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
        if fecha_inicio:
            df = df[df[col_fecha] >= pd.to_datetime(fecha_inicio)]
        if fecha_fin:
            df = df[df[col_fecha] <= pd.to_datetime(fecha_fin)]

    # 3. Identificación y Limpieza Numérica
    col_plan = next((c for c in ['cumple_planograma', 'status_planograma'] if c in df.columns), None)
    col_agot = next((c for c in ['cant_sku_agotados', 'agotados'] if c in df.columns), None)
    col_sku  = next((c for c in ['cant_sku', 'total_skus'] if c in df.columns), None)

    for col in [col_plan, col_agot, col_sku]:
        if col:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # ---------------------------------------------------------
    # 4. CÁLCULO DE TOTALES GLOBALES (Reactivos al filtro)
    # ---------------------------------------------------------
    total_visitas = len(df)

    # Cumplimiento promedio global
    global_cumplimiento = (df[col_plan].mean() * 100).round(2) if col_plan and not df.empty else 0

    # Agotados promedio global
    if col_agot and col_sku and df[col_sku].sum() > 0:
        global_agotados = ((df[col_agot].sum() / df[col_sku].sum()) * 100).round(2)
    else:
        global_agotados = 0

    resumen_global = {
        "visitas": total_visitas,
        "cumplimiento": global_cumplimiento,
        "agotados": global_agotados
    }

    # ---------------------------------------------------------
    # 5. AGRUPACIÓN PARA LA TABLA
    # ---------------------------------------------------------
    if agrupar_por == "cadena":
        cols_id = ['nombre_cadena']
    else:
        cols_id = ['nombre_cadena', 'nombre_pdv']

    # Mapa de agregación
    mapa_metricas = {'visitas': ('id', 'count')}
    if col_plan: mapa_metricas['cumple_planograma'] = (col_plan, 'sum')
    if col_agot: mapa_metricas['sku_agotados'] = (col_agot, 'sum')
    if col_sku:  mapa_metricas['total_sku'] = (col_sku, 'sum')

    # Ejecutar GroupBy
    df_grouped = df.groupby(cols_id).agg(**mapa_metricas).reset_index()

    # KPIs por fila (Tabla)
    if 'cumple_planograma' in df_grouped.columns:
        df_grouped['pct_cumplimiento'] = (df_grouped['cumple_planograma'] / df_grouped['visitas'] * 100).round(2)
    else:
        df_grouped['pct_cumplimiento'] = 0

    if 'sku_agotados' in df_grouped.columns and 'total_sku' in df_grouped.columns:
        df_grouped['pct_agotados'] = np.where(
            df_grouped['total_sku'] > 0,
            (df_grouped['sku_agotados'] / df_grouped['total_sku'] * 100).round(2),
            0
        )
    else:
        df_grouped['pct_agotados'] = 0

    # Ordenar por cumplimiento (críticos primero)
    df_grouped = df_grouped.sort_values(by='pct_cumplimiento', ascending=True)

    # 6. Retorno Estructurado
    return {
        "filas": df_grouped.to_dict(orient='records'),
        "totales": resumen_global
    }