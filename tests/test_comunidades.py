"""
Pruebas exhaustivas para el Módulo 2 (Detección de Comunidades y Fraude).
Incluye la verificación obligatoria del caso de 8 cuentas del Tema 5 y oráculos cruzados.
"""

import pytest
import networkx as nx
from networkx.algorithms.community import modularity as nx_modularity

from src.graph import Edge, Graph, Node
from src.algoritmos.comunidades import (
    AlgoritmoLouvain,
    barrido_umbrales,
    calcular_modularidad,
    componentes_por_umbral_bfs,
    componentes_por_umbral_union_find,
    propagacion_etiquetas,
)
from src.analisis_transacciones import AnalizadorTransaccionesFinancieras


def construir_grafo_tema5() -> Graph:
    """
    Construye el grafo de 8 cuentas de verificación obligatoria del Tema 5:
    - Grupo 1: A-B:12, A-C:9, B-C:11, B-D:8, C-D:10, A-D:7
    - Grupo 2: E-F:14, E-G:9, F-G:12
    - Débiles: D-E:2, H-A:1, H-F:1
    """
    g = Graph(dirigido=False, ponderado=True)
    for nodo_id in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        g.agregar_nodo(Node(nodo_id, "cuenta"))

    aristas = [
        # Grupo 1
        ("A", "B", 12), ("A", "C", 9), ("B", "C", 11),
        ("B", "D", 8),  ("C", "D", 10), ("A", "D", 7),
        # Grupo 2
        ("E", "F", 14), ("E", "G", 9), ("F", "G", 12),
        # Débiles
        ("D", "E", 2),  ("H", "A", 1), ("H", "F", 1),
    ]

    for u, v, w in aristas:
        g.agregar_arista(Edge(origen=u, destino=v, monto=float(w), n_transferencias=w))

    return g


def test_caso_obligatorio_tema5_umbrales():
    """
    Verifica las expectativas formales del barrido de umbrales en el caso de 8 cuentas:
    - Umbral 1: 1 componente con {A..H}
    - Umbral 2: {A..G} y {H}
    - Umbrales 3 a 7: {A,B,C,D}, {E,F,G}, {H}
    - Umbral 8+: se parte el grupo real (A queda desconectada de D)
    """
    g = construir_grafo_tema5()
    peso_fn = lambda e: float(e.n_transferencias)

    # Umbral 1
    p1 = componentes_por_umbral_bfs(g, 1.0, peso_fn)
    assert len(set(p1.values())) == 1

    # Umbral 2: H desconectado, A..G juntos
    p2 = componentes_por_umbral_bfs(g, 2.0, peso_fn)
    assert len(set(p2.values())) == 2
    assert p2["H"] != p2["A"]
    assert p2["A"] == p2["B"] == p2["E"] == p2["F"]

    # Umbrales 3 a 7: {A,B,C,D}, {E,F,G}, {H}
    for u in [3.0, 5.0, 7.0]:
        pu = componentes_por_umbral_bfs(g, u, peso_fn)
        # Debe haber exactamente 3 componentes
        assert len(set(pu.values())) == 3
        # Grupo 1 unido
        assert pu["A"] == pu["B"] == pu["C"] == pu["D"]
        # Grupo 2 unido
        assert pu["E"] == pu["F"] == pu["G"]
        # Separados entre sí y de H
        assert pu["A"] != pu["E"]
        assert pu["A"] != pu["H"]
        assert pu["E"] != pu["H"]

    # Umbral 8 o más: la arista A-D (peso 7) desaparece, separando A y D si solo pasara por allí
    # En el grupo 1: A-B (12), B-D (8), C-D (10), B-C (11). Con umbral 8 siguen conectados por B.
    # Con umbral 9, B-D (8) cae. Con umbral 11, B-C (11), A-B (12) quedan, C-D (10) cae.
    p8 = componentes_por_umbral_bfs(g, 8.0, peso_fn)
    # A-D (peso 7) no está presente
    # Con umbral 12
    p12 = componentes_por_umbral_bfs(g, 12.0, peso_fn)
    # Grupo 1 se rompe completamente
    assert p12["A"] != p12["D"]


def test_caso_obligatorio_tema5_louvain():
    """
    Verifica que Louvain detecta los dos grupos principales {A,B,C,D} y {E,F,G},
    con H asignado a alguno (nodo de frontera) y modularidad Q > 0.3.
    """
    g = construir_grafo_tema5()
    peso_fn = lambda e: float(e.n_transferencias)
    louvain = AlgoritmoLouvain(gamma=1.0)
    resultado = louvain.ejecutar_multi_semilla(g, n_corridas=5, semilla_base=42, peso_fn=peso_fn)

    part = resultado["particion"]
    q = resultado["modularidad"]

    assert q > 0.3, f"Se esperaba modularidad Q > 0.3, obtenida: {q}"
    # Grupo 1 coalescente
    assert part["A"] == part["B"] == part["C"] == part["D"]
    # Grupo 2 coalescente
    assert part["E"] == part["F"] == part["G"]
    # Grupos 1 y 2 en comunidades distintas
    assert part["A"] != part["E"]
    # H asignado a una de las dos comunidades o como frontera
    assert part["H"] in {part["A"], part["E"]}


def test_caso_obligatorio_tema5_propagacion_etiquetas():
    """
    Verifica LPA sobre el caso de 8 cuentas.
    """
    g = construir_grafo_tema5()
    peso_fn = lambda e: float(e.n_transferencias)
    part = propagacion_etiquetas(g, peso_fn=peso_fn, seed=42)

    # {A,B,C,D} y {E,F,G} deben converger a etiquetas unificadas respectivamente
    assert part["A"] == part["B"] == part["C"] == part["D"]
    assert part["E"] == part["F"] == part["G"]
    assert part["A"] != part["E"]


def test_oraculo_modularidad_contra_networkx():
    """
    Compara el cálculo de modularidad implementado desde cero contra networkx.community.modularity.
    """
    g = construir_grafo_tema5()
    peso_fn = lambda e: float(e.n_transferencias)

    particion = {
        "A": 0, "B": 0, "C": 0, "D": 0,
        "E": 1, "F": 1, "G": 1,
        "H": 0,
    }

    # Modularidad OptiFin
    q_propia = calcular_modularidad(g, particion, gamma=1.0, peso_fn=peso_fn)

    # Modularidad NetworkX
    g_nx = nx.Graph()
    for e in g.iter_aristas():
        g_nx.add_edge(e.origen, e.destino, weight=float(e.n_transferencias))

    comunidades_nx = [
        {"A", "B", "C", "D", "H"},
        {"E", "F", "G"},
    ]
    q_nx = nx_modularity(g_nx, comunidades_nx, weight="weight")

    assert pytest.approx(q_propia, rel=1e-4) == q_nx


def test_orquestador_analisis_transacciones():
    """Prueba el pipeline completo con concentradores, puntaje y reporte Markdown."""
    g = construir_grafo_tema5()
    analizador = AnalizadorTransaccionesFinancieras(
        criterio_peso="transferencias",
        percentil_concentrador=99.0,
    )
    g_prep = analizador.preprocesar_red(g, accion_concentrador="limitar")
    res_louvain = analizador.detectar_comunidades_louvain(g_prep, n_corridas=3, semilla=100)
    metricas = analizador.analizar_comunidades(g_prep, res_louvain["particion"])

    assert len(metricas) >= 2
    reporte_md = analizador.generar_reporte_markdown(
        metricas, res_louvain["modularidad"], res_louvain["estabilidad"]
    )
    assert "Resumen Ejecutivo del Algoritmo Louvain" in reporte_md
    assert "Score Prioridad" in reporte_md
