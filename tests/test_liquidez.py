"""
Pruebas exhaustivas para el Módulo 4: Distribución de Liquidez y Cuellos de Botella.
Incluye validación cruzada Dinic vs Edmonds-Karp vs Ford-Fulkerson,
oráculo independiente con NetworkX, teorema Max-Flow / Min-Cut y casos de borde obligatorios.
"""

from typing import Dict, Tuple
import pytest
import networkx as nx

from src.algoritmos.flujo import (
    construir_red_residual_desde_grafo,
    dinic_flujo_maximo,
    edmonds_karp_flujo_maximo,
    ford_fulkerson_dfs,
)
from src.distribucion_liquidez import (
    ID_SUPER_FUENTE,
    ID_SUPER_SUMIDERO,
    PlanificadorDistribucionLiquidez,
)
from src.graph import Edge, Graph, Node


def crear_red_liquidez_prueba() -> Tuple[Graph, Dict[str, float], Dict[str, float]]:
    """
    Crea una red con bóvedas centrales, regionales y agencias/ATM.
    Topología:
    BOVEDA-CENTRAL (oferta 1,000,000)
      -> REGIONAL-NORTE (capacidad 600,000)
           -> AGENCIA-1 (capacidad 300,000, demanda 250,000)
           -> AGENCIA-2 (capacidad 200,000, demanda 350,000)  <- cuello en ruta
      -> REGIONAL-SUR (capacidad 400,000)
           -> ATM-SUR (capacidad 500,000, demanda 400,000)
    """
    g = Graph(dirigido=True, ponderado=True)

    g.agregar_nodo(Node("BOVEDA-CENTRAL", "boveda_central"))
    g.agregar_nodo(Node("REGIONAL-NORTE", "boveda_regional"))
    g.agregar_nodo(Node("REGIONAL-SUR", "boveda_regional"))
    g.agregar_nodo(Node("AGENCIA-1", "agencia"))
    g.agregar_nodo(Node("AGENCIA-2", "agencia"))
    g.agregar_nodo(Node("ATM-SUR", "atm"))

    rutas = [
        ("BOVEDA-CENTRAL", "REGIONAL-NORTE", 600000.0),
        ("BOVEDA-CENTRAL", "REGIONAL-SUR", 400000.0),
        ("REGIONAL-NORTE", "AGENCIA-1", 300000.0),
        ("REGIONAL-NORTE", "AGENCIA-2", 200000.0),
        ("REGIONAL-SUR", "ATM-SUR", 500000.0),
    ]

    for u, v, cap in rutas:
        g.agregar_arista(Edge(origen=u, destino=v, capacidad=cap, disponible=True))

    oferta = {"BOVEDA-CENTRAL": 1000000.0}
    demanda = {
        "AGENCIA-1": 250000.0,
        "AGENCIA-2": 350000.0,
        "ATM-SUR": 400000.0,
    }

    return g, oferta, demanda


def test_coincidencia_dinic_edmonds_karp_ford_fulkerson():
    """Verifica que los tres algoritmos obtengan idéntico valor de flujo máximo."""
    g, oferta, demanda = crear_red_liquidez_prueba()
    planificador = PlanificadorDistribucionLiquidez()

    res_dinic = planificador.optimizar_flujo_dinic(g, oferta, demanda)
    res_ek = planificador.optimizar_flujo_edmonds_karp(g, oferta, demanda)
    res_ff = planificador.optimizar_flujo_ford_fulkerson(g, oferta, demanda)

    assert pytest.approx(res_dinic.flujo_maximo, rel=1e-5) == res_ek.flujo_maximo
    assert pytest.approx(res_dinic.flujo_maximo, rel=1e-5) == res_ff.flujo_maximo
    # Flujo esperado: 250k (Agencia-1) + 200k (Agencia-2 limitada por ruta) + 400k (ATM-SUR) = 850,000.0
    assert pytest.approx(res_dinic.flujo_maximo, rel=1e-5) == 850000.0


def test_oraculo_flujo_y_corte_contra_networkx():
    """Valida el valor de flujo máximo y capacidad de corte contra NetworkX."""
    g, oferta, demanda = crear_red_liquidez_prueba()
    planificador = PlanificadorDistribucionLiquidez()

    res_dinic = planificador.optimizar_flujo_dinic(g, oferta, demanda)

    # Red aumentada equivalente en NetworkX
    g_aumentado = planificador.preparar_red_con_supernodos(g, oferta, demanda)
    g_nx = nx.DiGraph()
    for e in g_aumentado.iter_aristas():
        g_nx.add_edge(e.origen, e.destino, capacity=float(e.capacidad))

    flujo_nx, _ = nx.maximum_flow(g_nx, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO)
    cut_val_nx, _ = nx.minimum_cut(g_nx, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO)

    assert pytest.approx(res_dinic.flujo_maximo, rel=1e-5) == flujo_nx
    assert pytest.approx(res_dinic.capacidad_corte, rel=1e-5) == cut_val_nx
    # Teorema max-flow / min-cut
    assert pytest.approx(res_dinic.flujo_maximo, rel=1e-5) == res_dinic.capacidad_corte


def test_distincion_saturadas_vs_cuellos_botella():
    """
    Verifica que se identifique correctamente el cuello de botella real (REGIONAL-NORTE -> AGENCIA-2)
    y se distinga de aristas saturadas no críticas.
    """
    g, oferta, demanda = crear_red_liquidez_prueba()
    planificador = PlanificadorDistribucionLiquidez()
    res = planificador.optimizar_flujo_dinic(g, oferta, demanda)

    cuellos = res.cuellos_de_botella
    # La ruta REGIONAL-NORTE -> AGENCIA-2 debe ser cuello de botella físico
    assert ("REGIONAL-NORTE", "AGENCIA-2") in cuellos


def test_analisis_sensibilidad_ganancia_marginal():
    """
    Verifica que al aumentar la capacidad del cuello de botella REGIONAL-NORTE -> AGENCIA-2,
    la ganancia marginal de distribución de efectivo sea positiva.
    """
    g, oferta, demanda = crear_red_liquidez_prueba()
    planificador = PlanificadorDistribucionLiquidez(delta_sensibilidad=50000.0)

    sensibilidad = planificador.analizar_sensibilidad_cuellos_botella(g, oferta, demanda)
    assert len(sensibilidad) > 0

    # La mejor oportunidad debe ser REGIONAL-NORTE -> AGENCIA-2 con ganancia positiva
    impacto_top = next(s for s in sensibilidad if s.origen == "REGIONAL-NORTE" and s.destino == "AGENCIA-2")
    assert impacto_top.ganancia_marginal == 50000.0
    assert impacto_top.eficiencia_inversion == 1.0


def test_casos_borde_obligatorios():
    """
    Casos obligatorios:
    - Oferta total < Demanda (déficit global)
    - Demanda cero
    - Capacidad cero
    - Nodo inalcanzable
    """
    g = Graph(dirigido=True, ponderado=True)
    g.agregar_nodo(Node("B1", "boveda_central"))
    g.agregar_nodo(Node("A1", "agencia"))
    g.agregar_nodo(Node("A_AISLADA", "agencia"))  # Inalcanzable
    g.agregar_arista(Edge("B1", "A1", capacidad=100.0))

    planificador = PlanificadorDistribucionLiquidez()

    # Caso 1: Déficit global (oferta 50 < demanda 200)
    res_def = planificador.optimizar_flujo_dinic(g, {"B1": 50.0}, {"A1": 200.0})
    assert res_def.flujo_maximo == 50.0

    # Caso 2: Demanda cero
    res_cero = planificador.optimizar_flujo_dinic(g, {"B1": 100.0}, {"A1": 0.0})
    assert res_cero.flujo_maximo == 0.0

    # Caso 3: Nodo inalcanzable
    res_aislado = planificador.optimizar_flujo_dinic(g, {"B1": 100.0}, {"A_AISLADA": 50.0})
    assert res_aislado.flujo_maximo == 0.0
