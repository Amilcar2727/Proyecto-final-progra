"""
Pruebas para Union-Find y algoritmos de recorridos (BFS, DFS, Puentes y Articulaciones).
"""

from src.algoritmos.union_find import UnionFind
from src.algoritmos.recorridos import (
    bfs_distancias,
    bfs_camino_mas_corto,
    dfs_recorrido,
    obtener_componentes_conexas,
    encontrar_puentes_y_articulaciones,
)
from src.graph import Edge, Graph


def test_union_find_operaciones():
    uf = UnionFind(["A", "B", "C", "D", "E"])
    assert uf.num_conjuntos == 5

    assert uf.union("A", "B") is True
    assert uf.union("B", "C") is True
    assert uf.union("A", "C") is False  # Ya conectados
    assert uf.conectados("A", "C") is True
    assert uf.num_conjuntos == 3

    assert uf.obtener_tamano_conjunto("A") == 3
    uf.union("D", "E")
    assert uf.num_conjuntos == 2


def test_recorridos_bfs_y_dfs():
    g = Graph(dirigido=False)
    # Grafo A - B - C - D
    g.agregar_arista(Edge("A", "B"))
    g.agregar_arista(Edge("B", "C"))
    g.agregar_arista(Edge("C", "D"))
    g.agregar_arista(Edge("A", "C"))  # Atajo

    camino = bfs_camino_mas_corto(g, "A", "D")
    assert camino == ["A", "C", "D"]

    distancias = bfs_distancias(g, "A")
    assert distancias["A"] == 0
    assert distancias["B"] == 1
    assert distancias["C"] == 1
    assert distancias["D"] == 2

    orden_dfs = dfs_recorrido(g, "A")
    assert len(orden_dfs) == 4
    assert set(orden_dfs) == {"A", "B", "C", "D"}


def test_puentes_y_puntos_articulacion():
    # Grafo con puente evidente:
    # Triángulo (A-B-C) conectado por puente (C-D) a otro triángulo (D-E-F)
    g = Graph(dirigido=False)
    g.agregar_arista(Edge("A", "B"))
    g.agregar_arista(Edge("B", "C"))
    g.agregar_arista(Edge("A", "C"))
    # Puente
    g.agregar_arista(Edge("C", "D"))
    # Segundo triángulo
    g.agregar_arista(Edge("D", "E"))
    g.agregar_arista(Edge("E", "F"))
    g.agregar_arista(Edge("D", "F"))

    puentes, articulaciones = encontrar_puentes_y_articulaciones(g)

    # El único puente debe ser (C, D)
    assert ("C", "D") in puentes or ("D", "C") in puentes
    assert len(puentes) == 1

    # Los puntos de articulación son C y D
    assert "C" in articulaciones
    assert "D" in articulaciones
    assert len(articulaciones) == 2
