"""
Algoritmos de Árbol de Expansión Mínima (MST / MSF) implementados desde cero:
1. Kruskal con Union-Find (compresión de caminos y unión por rango) - O(E log E).
2. Prim con min-heap binario (heapq) - O(E log V).

Ambos algoritmos:
- Admiten funciones de ponderación arbitrarias.
- Soportan grafos no conexos, retornando un Bosque de Expansión Mínima (MSF).
- Soportan restricciones de aristas obligatorias y aristas prohibidas/no disponibles.
"""

from __future__ import annotations
import heapq
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.algoritmos.union_find import UnionFind
from src.graph import Edge, Graph


@dataclass
class ResultadoMST:
    """Resultado estructurado de la ejecución de un algoritmo de expansión mínima."""
    aristas_mst: List[Edge]
    peso_total: float
    num_componentes: int
    componentes: List[Set[str]]
    aristas_por_componente: Dict[int, List[Edge]]
    orden_seleccion: List[Tuple[str, str, float]]


def kruskal_mst(
    grafo: Graph,
    peso_fn: Optional[Callable[[Edge], float]] = None,
    aristas_obligatorias: Optional[Set[Tuple[str, str]]] = None,
    aristas_prohibidas: Optional[Set[Tuple[str, str]]] = None,
) -> ResultadoMST:
    """
    Algoritmo de Kruskal con Union-Find para Árbol/Bosque de Expansión Mínima.

    Complejidad:
    - Temporal: O(E log E) debido al ordenamiento de aristas.
    - Espacial: O(V + E) para la estructura de conjuntos disjuntos y aristas.
    """
    if peso_fn is None:
        peso_fn = lambda e: e.costo_instalacion + e.costo_operativo

    obligatorias = set()
    if aristas_obligatorias:
        for u, v in aristas_obligatorias:
            obligatorias.add((min(u, v), max(u, v)))

    prohibidas = set()
    if aristas_prohibidas:
        for u, v in aristas_prohibidas:
            prohibidas.add((min(u, v), max(u, v)))

    nodos = list(grafo.nodes.keys())
    uf = UnionFind(nodos)
    aristas_seleccionadas: List[Edge] = []
    orden_seleccion: List[Tuple[str, str, float]] = []
    peso_acumulado = 0.0

    # 1. Procesar aristas candidatas
    candidatas_obligatorias: List[Tuple[float, int, Edge]] = []
    candidatas_regulares: List[Tuple[float, int, Edge]] = []

    for idx, e in enumerate(grafo.iter_aristas()):
        if not e.disponible:
            continue
        par = (min(e.origen, e.destino), max(e.origen, e.destino))
        if par in prohibidas:
            continue

        w = float(peso_fn(e))
        if par in obligatorias:
            candidatas_obligatorias.append((w, idx, e))
        else:
            candidatas_regulares.append((w, idx, e))

    # Incluir primero las obligatorias si no forman ciclo entre sí
    for w, _, e in candidatas_obligatorias:
        if uf.union(e.origen, e.destino):
            aristas_seleccionadas.append(e)
            orden_seleccion.append((e.origen, e.destino, w))
            peso_acumulado += w

    # 2. Ordenar aristas regulares por peso ascendente
    candidatas_regulares.sort(key=lambda item: item[0])

    for w, _, e in candidatas_regulares:
        if uf.union(e.origen, e.destino):
            aristas_seleccionadas.append(e)
            orden_seleccion.append((e.origen, e.destino, w))
            peso_acumulado += w

    # Identificar componentes resultantes
    componentes_dict = uf.obtener_componentes()
    componentes_lista = [set(miembros) for miembros in componentes_dict.values()]

    # Clasificar aristas por componente
    comp_map = {}
    for c_idx, comp_set in enumerate(componentes_lista):
        for nodo in comp_set:
            comp_map[nodo] = c_idx

    aristas_por_comp: Dict[int, List[Edge]] = {i: [] for i in range(len(componentes_lista))}
    for e in aristas_seleccionadas:
        cid = comp_map[e.origen]
        aristas_por_comp[cid].append(e)

    return ResultadoMST(
        aristas_mst=aristas_seleccionadas,
        peso_total=peso_acumulado,
        num_componentes=len(componentes_lista),
        componentes=componentes_lista,
        aristas_por_componente=aristas_por_comp,
        orden_seleccion=orden_seleccion,
    )


def prim_mst(
    grafo: Graph,
    peso_fn: Optional[Callable[[Edge], float]] = None,
    nodo_inicio: Optional[str] = None,
) -> ResultadoMST:
    """
    Algoritmo de Prim utilizando min-heap binario (heapq) para Bosque de Expansión Mínima.

    Complejidad:
    - Temporal: O(E log V).
    - Espacial: O(V + E).
    """
    if peso_fn is None:
        peso_fn = lambda e: e.costo_instalacion + e.costo_operativo

    visitados: Set[str] = set()
    aristas_seleccionadas: List[Edge] = []
    orden_seleccion: List[Tuple[str, str, float]] = []
    peso_acumulado = 0.0

    # Construir lista de adyacencia no dirigida
    adj_no_dir: Dict[str, List[Tuple[str, float, Edge]]] = {n: [] for n in grafo.nodes}
    for e in grafo.iter_aristas():
        if not e.disponible:
            continue
        w = float(peso_fn(e))
        adj_no_dir[e.origen].append((e.destino, w, e))
        if e.origen != e.destino:
            adj_no_dir[e.destino].append((e.origen, w, e))

    nodos_a_visitar = list(grafo.nodes.keys())
    if nodo_inicio and nodo_inicio in grafo.nodes:
        # Colocar nodo_inicio primero
        nodos_a_visitar.remove(nodo_inicio)
        nodos_a_visitar.insert(0, nodo_inicio)

    for raiz in nodos_a_visitar:
        if raiz in visitados:
            continue

        visitados.add(raiz)
        heap: List[Tuple[float, int, str, str, Edge]] = []
        contador = 0

        for dest, w, edge in adj_no_dir[raiz]:
            contador += 1
            heapq.heappush(heap, (w, contador, raiz, dest, edge))

        while heap:
            w, _, u, v, edge = heapq.heappop(heap)
            if v in visitados:
                continue

            visitados.add(v)
            aristas_seleccionadas.append(edge)
            orden_seleccion.append((edge.origen, edge.destino, w))
            peso_acumulado += w

            for prox, peso_prox, edge_prox in adj_no_dir[v]:
                if prox not in visitados:
                    contador += 1
                    heapq.heappush(heap, (peso_prox, contador, v, prox, edge_prox))

    # Identificar componentes conectadas por el resultado
    uf = UnionFind(grafo.nodes.keys())
    for e in aristas_seleccionadas:
        uf.union(e.origen, e.destino)

    componentes_dict = uf.obtener_componentes()
    componentes_lista = [set(miembros) for miembros in componentes_dict.values()]
    comp_map = {n: i for i, s in enumerate(componentes_lista) for n in s}

    aristas_por_comp: Dict[int, List[Edge]] = {i: [] for i in range(len(componentes_lista))}
    for e in aristas_seleccionadas:
        cid = comp_map[e.origen]
        aristas_por_comp[cid].append(e)

    return ResultadoMST(
        aristas_mst=aristas_seleccionadas,
        peso_total=peso_acumulado,
        num_componentes=len(componentes_lista),
        componentes=componentes_lista,
        aristas_por_componente=aristas_por_comp,
        orden_seleccion=orden_seleccion,
    )
