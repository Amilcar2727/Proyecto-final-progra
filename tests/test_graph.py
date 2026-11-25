"""
Pruebas unitarias para la estructura central Graph, Node y Edge.
"""

import pytest
from src.graph import Edge, Graph, Node


def test_node_creacion_y_validaciones():
    n = Node(id="CTA-01", tipo="cuenta", atributos={"saldo": 5000.0})
    assert n.id == "CTA-01"
    assert n.tipo == "cuenta"
    assert n.get("saldo") == 5000.0
    n.set("bloqueada", True)
    assert n.get("bloqueada") is True

    with pytest.raises(ValueError, match="Tipo de nodo 'invalido' no válido"):
        Node(id="CTA-02", tipo="invalido")


def test_edge_validaciones_invariantes():
    e = Edge(origen="A", destino="B", monto=150.0, riesgo=0.25)
    assert e.origen == "A"
    assert e.monto == 150.0

    with pytest.raises(ValueError, match="monto no puede ser negativo"):
        Edge(origen="A", destino="B", monto=-10.0)

    with pytest.raises(ValueError, match="riesgo debe estar acotado"):
        Edge(origen="A", destino="B", riesgo=1.5)


def test_graph_operaciones_basicas_dirigido():
    g = Graph(dirigido=True)
    g.agregar_nodo(Node("A", "banco" if False else "cuenta"))
    g.agregar_nodo(Node("B", "agencia"))

    g.agregar_arista(Edge("A", "B", monto=100.0))
    g.agregar_arista(Edge("B", "A", monto=50.0))

    assert g.num_nodos == 2
    assert g.num_aristas == 2
    assert g.vecinos("A") == ["B"]
    assert g.vecinos("B") == ["A"]
    assert g.grado_salida("A") == 1
    assert g.grado_entrada("A") == 1

    # Eliminación de nodo y cascada de aristas
    g.eliminar_nodo("B")
    assert not g.existe_nodo("B")
    assert g.num_nodos == 1
    assert g.num_aristas == 0


def test_graph_no_dirigido_y_colapso():
    g_dir = Graph(dirigido=True)
    g_dir.agregar_arista(Edge("X", "Y", monto=30.0, n_transferencias=2))
    g_dir.agregar_arista(Edge("Y", "X", monto=70.0, n_transferencias=3))

    g_colapsado = g_dir.a_no_dirigido(agregar=sum)
    assert not g_colapsado.dirigido
    assert g_colapsado.num_nodos == 2
    assert g_colapsado.num_aristas == 1

    aristas_xy = g_colapsado.obtener_aristas("X", "Y")
    assert len(aristas_xy) == 1
    assert aristas_xy[0].monto == 100.0
    assert aristas_xy[0].n_transferencias == 5


def test_graph_transpuesto_y_copia():
    g = Graph(dirigido=True)
    g.agregar_arista(Edge("A", "B", monto=10.0))
    g.agregar_arista(Edge("B", "C", monto=20.0))

    gt = g.transpuesto()
    assert gt.vecinos("B") == ["A"]
    assert gt.vecinos("C") == ["B"]
    assert gt.vecinos("A") == []

    copia = g.copiar()
    assert copia.num_nodos == g.num_nodos
    assert copia.num_aristas == g.num_aristas
    copia.eliminar_nodo("A")
    assert g.existe_nodo("A")
    assert not copia.existe_nodo("A")
