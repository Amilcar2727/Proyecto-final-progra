"""
Algoritmos fundamentales de recorrido y análisis topológico en grafos:
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- Detección de caminos más cortos no ponderados
- Componentes conexas
- Detección de puentes y puntos de articulación (algoritmo de Tarjan / low-link)

Complejidades:
- BFS / DFS / Componentes: O(V + E) tiempo, O(V) espacio.
- Puentes y articulaciones: O(V + E) tiempo, O(V) espacio.
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple
from src.graph import Graph


def bfs_distancias(grafo: Graph, origen: str) -> Dict[str, int]:
    """
    Calcula distancias mínimas en cantidad de saltos desde 'origen' a todos
    los nodos alcanzables usando BFS.

    Complejidad: O(V + E) tiempo, O(V) espacio.
    """
    if not grafo.existe_nodo(origen):
        raise KeyError(f"Nodo origen '{origen}' no existe en el grafo.")

    distancias: Dict[str, int] = {origen: 0}
    cola = deque([origen])

    while cola:
        u = cola.popleft()
        d_actual = distancias[u]
        for v in grafo.vecinos(u):
            if v not in distancias:
                distancias[v] = d_actual + 1
                cola.append(v)

    return distancias


def bfs_camino_mas_corto(grafo: Graph, origen: str, destino: str) -> Optional[List[str]]:
    """
    Encuentra el camino con menor número de saltos entre origen y destino.
    Retorna la lista de nodos [origen, ..., destino] o None si no hay camino.

    Complejidad: O(V + E) tiempo, O(V) espacio.
    """
    if not grafo.existe_nodo(origen) or not grafo.existe_nodo(destino):
        return None
    if origen == destino:
        return [origen]

    padres: Dict[str, Optional[str]] = {origen: None}
    cola = deque([origen])

    while cola:
        u = cola.popleft()
        if u == destino:
            break
        for v in grafo.vecinos(u):
            if v not in padres:
                padres[v] = u
                cola.append(v)

    if destino not in padres:
        return None

    camino = []
    curr: Optional[str] = destino
    while curr is not None:
        camino.append(curr)
        curr = padres[curr]
    camino.reverse()
    return camino


def dfs_recorrido(grafo: Graph, origen: str) -> List[str]:
    """
    Recorrido en profundidad (DFS) iterativo desde el nodo origen.

    Complejidad: O(V + E) tiempo, O(V) espacio.
    """
    if not grafo.existe_nodo(origen):
        raise KeyError(f"Nodo origen '{origen}' no existe en el grafo.")

    visitados: Set[str] = set()
    orden: List[str] = []
    pila = [origen]

    while pila:
        u = pila.pop()
        if u not in visitados:
            visitados.add(u)
            orden.append(u)
            # Agregar vecinos en orden reverso para recorrer en orden natural
            for v in reversed(grafo.vecinos(u)):
                if v not in visitados:
                    pila.append(v)

    return orden


def obtener_componentes_conexas(grafo: Graph) -> List[Set[str]]:
    """
    Identifica todas las componentes conexas de un grafo no dirigido.
    Si el grafo es dirigido, opera sobre su versión no dirigida.

    Complejidad: O(V + E) tiempo, O(V) espacio.
    """
    visitados: Set[str] = set()
    componentes: List[Set[str]] = []

    for nodo_id in grafo.nodes:
        if nodo_id not in visitados:
            comp: Set[str] = set()
            cola = deque([nodo_id])
            visitados.add(nodo_id)
            while cola:
                u = cola.popleft()
                comp.add(u)
                vecinos = set(grafo.vecinos(u))
                if grafo.dirigido:
                    vecinos.update(grafo.predecesores(u))
                for v in vecinos:
                    if v not in visitados:
                        visitados.add(v)
                        cola.append(v)
            componentes.append(comp)

    return componentes


def encontrar_puentes_y_articulaciones(
    grafo: Graph,
) -> Tuple[List[Tuple[str, str]], Set[str]]:
    """
    Encuentra todos los puentes (aristas críticas cuya remoción desconecta el grafo)
    y puntos de articulación (nodos críticos cuya falla parte la red) en un grafo no dirigido
    utilizando el algoritmo de Tarjan basado en discovery time y low-link.

    Complejidad: O(V + E) tiempo, O(V) espacio.

    Returns:
        Tupla (puentes, puntos_articulacion):
        - puentes: lista de tuplas (u, v) con u < v
        - puntos_articulacion: conjunto de IDs de nodos críticos
    """
    tiempo = 0
    discovery: Dict[str, int] = {}
    low: Dict[str, int] = {}
    padre: Dict[str, Optional[str]] = {}
    articulaciones: Set[str] = set()
    puentes: List[Tuple[str, str]] = []

    # Construir lista de adyacencia no dirigida
    adj_no_dirigida: Dict[str, Set[str]] = {n: set() for n in grafo.nodes}
    for e in grafo.iter_aristas():
        if e.origen != e.destino:
            adj_no_dirigida[e.origen].add(e.destino)
            adj_no_dirigida[e.destino].add(e.origen)

    for inicio in grafo.nodes:
        if inicio not in discovery:
            # DFS con llamada recursiva / pila explícita
            # Usamos recursión para claridad matemática respetando límite de profundidad
            def dfs_visitar(u: str) -> None:
                nonlocal tiempo
                tiempo += 1
                discovery[u] = low[u] = tiempo
                hijos = 0

                for v in adj_no_dirigida[u]:
                    if v not in discovery:
                        padre[v] = u
                        hijos += 1
                        dfs_visitar(v)

                        low[u] = min(low[u], low[v])

                        # Condición 1 de articulación: raíz con ≥ 2 hijos
                        if padre[u] is None and hijos > 1:
                            articulaciones.add(u)

                        # Condición 2 de articulación: no-raíz con hijo sin back-edge
                        if padre[u] is not None and low[v] >= discovery[u]:
                            articulaciones.add(u)

                        # Condición de puente: low[v] estrictamente mayor a discovery[u]
                        if low[v] > discovery[u]:
                            puentes.append((min(u, v), max(u, v)))

                    elif v != padre.get(u):
                        low[u] = min(low[u], discovery[v])

            padre[inicio] = None
            dfs_visitar(inicio)

    return sorted(list(set(puentes))), articulaciones
