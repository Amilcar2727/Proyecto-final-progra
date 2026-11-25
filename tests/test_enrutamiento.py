"""
Pruebas exhaustivas para el Módulo 3: Enrutamiento Troncal de Menor Costo (MST).
Incluye validación cruzada entre Kruskal y Prim, oráculo independiente con NetworkX,
restricciones what-if, análisis de fragilidad y comparación de rutas.
"""

import pytest
import networkx as nx

from src.algoritmos.arbol_expansion import kruskal_mst, prim_mst
from src.enrutamiento_financiero import OptimizadorRedTroncal
from src.graph import Edge, Graph, Node


def crear_red_troncal_prueba() -> Graph:
    """
    Crea una red financiera sintética con 6 nodos (sedes, agencias, ATM)
    con múltiples alternativas de enlace.
    """
    g = Graph(dirigido=False, ponderado=True)
    nodos = [
        Node("SEDE-CENTRAL", "entidad"),
        Node("AGENCIA-NORTE", "agencia"),
        Node("AGENCIA-SUR", "agencia"),
        Node("AGENCIA-ESTE", "agencia"),
        Node("ATM-PLAZA", "atm"),
        Node("ATM-CENTRO", "atm"),
    ]
    for n in nodos:
        g.agregar_nodo(n)

    enlaces = [
        ("SEDE-CENTRAL", "AGENCIA-NORTE", 1000.0, 50.0, 10.0),
        ("SEDE-CENTRAL", "AGENCIA-SUR", 1500.0, 70.0, 15.0),
        ("SEDE-CENTRAL", "AGENCIA-ESTE", 1200.0, 60.0, 12.0),
        ("AGENCIA-NORTE", "AGENCIA-ESTE", 800.0, 40.0, 8.0),
        ("AGENCIA-SUR", "AGENCIA-ESTE", 900.0, 45.0, 9.0),
        ("AGENCIA-NORTE", "ATM-CENTRO", 400.0, 20.0, 5.0),
        ("AGENCIA-ESTE", "ATM-PLAZA", 500.0, 25.0, 6.0),
        ("ATM-CENTRO", "ATM-PLAZA", 600.0, 30.0, 7.0),
        ("AGENCIA-SUR", "ATM-PLAZA", 1100.0, 55.0, 14.0),
    ]

    for u, v, capex, opex, lat in enlaces:
        g.agregar_arista(
            Edge(
                origen=u,
                destino=v,
                costo_instalacion=capex,
                costo_operativo=opex,
                tiempo=lat,
                disponible=True,
            )
        )

    return g


def test_coincidencia_kruskal_y_prim():
    """Verifica que Kruskal y Prim produzcan exactamente el mismo peso total."""
    g = crear_red_troncal_prueba()
    optimizador = OptimizadorRedTroncal(horizonte_meses=12.0)

    res_kruskal = optimizador.ejecutar_kruskal(g)
    res_prim = optimizador.ejecutar_prim(g)

    assert pytest.approx(res_kruskal.peso_total, rel=1e-5) == res_prim.peso_total
    assert res_kruskal.num_componentes == 1
    assert len(res_kruskal.aristas_mst) == g.num_nodos - 1
    assert len(res_prim.aristas_mst) == g.num_nodos - 1


def test_oraculo_mst_contra_networkx():
    """Valida el costo del MST obtenido frente a networkx.minimum_spanning_tree."""
    g = crear_red_troncal_prueba()
    optimizador = OptimizadorRedTroncal(horizonte_meses=12.0)

    res_kruskal = optimizador.ejecutar_kruskal(g)

    # Construir grafo NetworkX equivalente
    g_nx = nx.Graph()
    for e in g.iter_aristas():
        peso = optimizador.funcion_costo(e)
        g_nx.add_edge(e.origen, e.destino, weight=peso)

    mst_nx = nx.minimum_spanning_tree(g_nx, weight="weight")
    peso_nx = mst_nx.size(weight="weight")

    assert pytest.approx(res_kruskal.peso_total, rel=1e-5) == peso_nx


def test_kruskal_con_aristas_obligatorias_y_prohibidas():
    """Evalúa escenarios 'what-if' con enlaces obligatorios forzados y prohibidos."""
    g = crear_red_troncal_prueba()
    optimizador = OptimizadorRedTroncal(horizonte_meses=12.0)

    # Forzar arista cara SEDE-CENTRAL - AGENCIA-SUR como obligatoria
    obligatorias = {("SEDE-CENTRAL", "AGENCIA-SUR")}
    # Prohibir arista barata AGENCIA-NORTE - ATM-CENTRO
    prohibidas = {("AGENCIA-NORTE", "ATM-CENTRO")}

    res = optimizador.ejecutar_kruskal(g, obligatorias=obligatorias, prohibidas=prohibidas)

    pares_seleccionados = {
        (min(e.origen, e.destino), max(e.origen, e.destino))
        for e in res.aristas_mst
    }

    assert ("AGENCIA-SUR", "SEDE-CENTRAL") in pares_seleccionados or ("SEDE-CENTRAL", "AGENCIA-SUR") in pares_seleccionados
    assert ("AGENCIA-NORTE", "ATM-CENTRO") not in pares_seleccionados


def test_red_desconectada_bosque_expansion():
    """Verifica que ante un grafo no conexo retorne un bosque con el número exacto de componentes."""
    g = crear_red_troncal_prueba()
    # Agregar una isla desconectada
    g.agregar_nodo(Node("AGENCIA-ISLA", "agencia"))
    g.agregar_nodo(Node("ATM-ISLA", "atm"))
    g.agregar_arista(Edge("AGENCIA-ISLA", "ATM-ISLA", costo_instalacion=100.0, costo_operativo=10.0))

    optimizador = OptimizadorRedTroncal(horizonte_meses=12.0)
    res = optimizador.ejecutar_kruskal(g)

    assert res.num_componentes == 2
    assert len(res.aristas_mst) == g.num_nodos - 2


def test_analisis_fragilidad_y_ahorro():
    """Verifica el cálculo de puentes, puntos de articulación y ahorro económico."""
    g = crear_red_troncal_prueba()
    optimizador = OptimizadorRedTroncal(horizonte_meses=12.0)

    res = optimizador.ejecutar_kruskal(g)
    fragilidad = optimizador.analizar_fragilidad(g, res)
    ahorro = optimizador.calcular_ahorro_economico(g, res)

    assert fragilidad["total_puentes"] == len(res.aristas_mst)  # En árbol toda arista es puente
    assert fragilidad["total_articulaciones"] > 0
    assert ahorro["ahorro_absoluto"] > 0
    assert ahorro["porcentaje_ahorro"] > 0

    ruta_info = optimizador.consultar_ruta_troncal(g, res, "ATM-CENTRO", "SEDE-CENTRAL")
    assert ruta_info["camino_mst"] is not None
    assert ruta_info["camino_mst"][0] == "ATM-CENTRO"
    assert ruta_info["camino_mst"][-1] == "SEDE-CENTRAL"
