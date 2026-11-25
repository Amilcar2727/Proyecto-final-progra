"""
Pruebas de gestión, serialización y validación de redes financieras (Módulo 1).
"""

import os
import tempfile
import pytest

from src.gestion_red import (
    GestorRedFinanciera,
    ErrorValidacionRed,
    ErrorArchivoInvalido,
)
from src.graph import Edge, Graph, Node


def test_carga_csv_valido_y_exportacion():
    csv_contenido = (
        "origen,destino,monto,n_transferencias,comision,capacidad,riesgo,disponible,canal\n"
        "CTA-101,CTA-102,500.0,2,5.0,1000.0,0.1,true,spei\n"
        "CTA-102,CTA-103,300.0,1,3.0,1000.0,0.05,true,spei\n"
    )
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write(csv_contenido)
        tmp_path = tmp.name

    try:
        gestor = GestorRedFinanciera()
        grafo = gestor.cargar_desde_csv(tmp_path, dirigido=True, estricto=True)
        assert grafo.num_nodos == 3
        assert grafo.num_aristas == 2
        assert len(gestor.errores_registro) == 0

        # Probar exportación a JSON y recarga
        json_path = tmp_path.replace(".csv", ".json")
        gestor.exportar_a_json(json_path)
        assert os.path.exists(json_path)

        gestor2 = GestorRedFinanciera()
        grafo2 = gestor2.cargar_desde_json(json_path, estricto=True)
        assert grafo2.num_nodos == 3
        assert grafo2.num_aristas == 2
        os.remove(json_path)
    finally:
        os.remove(tmp_path)


def test_validacion_estricta_falla_con_errores_registrados():
    csv_invalido = (
        "origen,destino,monto,riesgo\n"
        "CTA-A,CTA-B,-50.0,0.2\n"  # Monto negativo
        "CTA-B,CTA-C,100.0,1.8\n"  # Riesgo > 1.0
        ",CTA-D,10.0,0.1\n"        # Origen ausente
    )
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write(csv_invalido)
        tmp_path = tmp.name

    try:
        gestor = GestorRedFinanciera()
        with pytest.raises(ErrorValidacionRed) as exc_info:
            gestor.cargar_desde_csv(tmp_path, estricto=True)
        assert len(exc_info.value.errores) >= 3

        # Modo tolerante debe cargar aristas válidas si existen
        grafo_tol = gestor.cargar_desde_csv(tmp_path, estricto=False)
        assert len(gestor.errores_registro) >= 3
    finally:
        os.remove(tmp_path)
