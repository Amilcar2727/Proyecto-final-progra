"""
Algoritmos de Flujo Máximo y Corte Mínimo implementados desde cero:
1. Dinic con grafos de nivel (BFS) y bloqueo de caminos con punteros de avance (DFS) - O(V² E).
2. Edmonds-Karp con caminos aumentantes por BFS - O(V E²).
3. Ford-Fulkerson con caminos aumentantes por DFS estándar - O(E * f).
4. Extracción de Corte Mínimo bipartito residual y verificación del teorema Max-Flow / Min-Cut.
5. Distinción matemática entre aristas saturadas y cuellos de botella del corte mínimo.

Complejidades:
- Dinic: O(V² E) tiempo, O(V + E) espacio.
- Edmonds-Karp: O(V E²) tiempo, O(V + E) espacio.
- Ford-Fulkerson: O(E * f) tiempo, O(V + E) espacio.
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.graph import Edge, Graph


@dataclass
class AristaResidual:
    """Arista en la red residual para algoritmos de flujo."""
    u: str
    v: str
    capacidad: float
    flujo: float = 0.0
    es_residual: bool = False
    inversa_idx: int = -1

    @property
    def residual(self) -> float:
        return self.capacidad - self.flujo


@dataclass
class ResultadoFlujo:
    """Resultado estructurado de la ejecución de flujo máximo."""
    flujo_maximo: float
    flujo_aristas: Dict[Tuple[str, str], float]
    corte_minimo: List[Tuple[str, str]]
    capacidad_corte: float
    nodos_fuente_s: Set[str]
    nodos_sumidero_t: Set[str]
    aristas_saturadas: List[Tuple[str, str]]
    cuellos_de_botella: List[Tuple[str, str]]
    conservacion_valida: bool
    capacidades_respetadas: bool


class RedResidual:
    """
    Grafo residual compacto con lista de adyacencia e indexación de aristas inversas.
    """

    def __init__(self, nodos: Set[str]) -> None:
        self.nodos = sorted(list(nodos))
        self.adj: Dict[str, List[AristaResidual]] = {n: [] for n in self.nodos}

    def agregar_arista(self, u: str, v: str, capacidad: float) -> None:
        """Agrega arista directa y residual inversa con capacidad 0."""
        if u not in self.adj:
            self.adj[u] = []
            self.nodos.append(u)
        if v not in self.adj:
            self.adj[v] = []
            self.nodos.append(v)

        idx_directa = len(self.adj[u])
        idx_inversa = len(self.adj[v])

        directa = AristaResidual(u=u, v=v, capacidad=capacidad, flujo=0.0, es_residual=False, inversa_idx=idx_inversa)
        inversa = AristaResidual(u=v, v=u, capacidad=0.0, flujo=0.0, es_residual=True, inversa_idx=idx_directa)

        self.adj[u].append(directa)
        self.adj[v].append(inversa)


def construir_red_residual_desde_grafo(
    grafo: Graph,
    fuente: str,
    sumidero: str,
) -> RedResidual:
    """Construye la estructura de red residual a partir de un objeto Graph."""
    todos_nodos = set(grafo.nodes.keys())
    todos_nodos.add(fuente)
    todos_nodos.add(sumidero)

    red = RedResidual(todos_nodos)

    # Acumular capacidades entre pares u->v por si hay aristas múltiples
    capacidades_agregadas: Dict[Tuple[str, str], float] = {}
    for e in grafo.iter_aristas():
        if not e.disponible or e.capacidad <= 0:
            continue
        par = (e.origen, e.destino)
        capacidades_agregadas[par] = capacidades_agregadas.get(par, 0.0) + e.capacidad
        if not grafo.dirigido and e.origen != e.destino:
            par_inv = (e.destino, e.origen)
            capacidades_agregadas[par_inv] = capacidades_agregadas.get(par_inv, 0.0) + e.capacidad

    for (u, v), cap in capacidades_agregadas.items():
        red.agregar_arista(u, v, cap)

    return red


def _extraer_corte_y_metricas(
    red: RedResidual,
    fuente: str,
    sumidero: str,
    flujo_maximo: float,
) -> ResultadoFlujo:
    """
    Identifica el corte mínimo bipartito residual (S_cut, T_cut),
    clasifica aristas saturadas vs cuellos de botella y valida conservación de flujo.
    """
    # BFS en grafo residual desde fuente usando solo aristas con capacidad residual > 0
    alcanzables: Set[str] = {fuente}
    cola = deque([fuente])

    while cola:
        u = cola.popleft()
        for arista in red.adj.get(u, []):
            if arista.residual > 1e-9 and arista.v not in alcanzables:
                alcanzables.add(arista.v)
                cola.append(arista.v)

    no_alcanzables = set(red.nodos) - alcanzables

    # Mapeo de flujos y verificación
    flujos: Dict[Tuple[str, str], float] = {}
    aristas_saturadas: List[Tuple[str, str]] = []
    cuellos_de_botella: List[Tuple[str, str]] = []
    capacidad_corte = 0.0
    capacidades_respetadas = True

    for u in red.adj:
        for arista in red.adj[u]:
            if not arista.es_residual:
                flujos[(arista.u, arista.v)] = arista.flujo
                if arista.flujo > arista.capacidad + 1e-7:
                    capacidades_respetadas = False

                # Saturada: flujo == capacidad y capacidad > 0
                if arista.capacidad > 0 and abs(arista.flujo - arista.capacidad) < 1e-7:
                    aristas_saturadas.append((arista.u, arista.v))

                # Corte mínimo: origen en alcanzables, destino en no alcanzables
                if arista.u in alcanzables and arista.v in no_alcanzables:
                    cuellos_de_botella.append((arista.u, arista.v))
                    capacidad_corte += arista.capacidad

    # Validar conservación de flujo en nodos intermedios (excluyendo fuente y sumidero)
    conservacion_valida = True
    for nodo in red.nodos:
        if nodo in (fuente, sumidero):
            continue
        flujo_entrante = sum(
            a.flujo for u in red.adj for a in red.adj[u] if not a.es_residual and a.v == nodo
        )
        flujo_saliente = sum(
            a.flujo for a in red.adj[nodo] if not a.es_residual
        )
        if abs(flujo_entrante - flujo_saliente) > 1e-6:
            conservacion_valida = False

    return ResultadoFlujo(
        flujo_maximo=flujo_maximo,
        flujo_aristas=flujos,
        corte_minimo=cuellos_de_botella,
        capacidad_corte=capacidad_corte,
        nodos_fuente_s=alcanzables,
        nodos_sumidero_t=no_alcanzables,
        aristas_saturadas=aristas_saturadas,
        cuellos_de_botella=cuellos_de_botella,
        conservacion_valida=conservacion_valida,
        capacidades_respetadas=capacidades_respetadas,
    )


def dinic_flujo_maximo(
    red: RedResidual,
    fuente: str,
    sumidero: str,
) -> ResultadoFlujo:
    """
    Algoritmo de Dinic implementado desde cero.
    Utiliza BFS para construir grafos de nivel y DFS con punteros de avance (work)
    para saturar caminos aumentantes en O(V² E).
    """
    flujo_total = 0.0

    while True:
        # 1. BFS para construir vector de niveles
        niveles: Dict[str, int] = {fuente: 0}
        cola = deque([fuente])

        while cola:
            u = cola.popleft()
            for arista in red.adj[u]:
                if arista.residual > 1e-9 and arista.v not in niveles:
                    niveles[arista.v] = niveles[u] + 1
                    cola.append(arista.v)

        if sumidero not in niveles:
            break  # Sumidero no alcanzable en grafo residual: optimalidad alcanzada

        # 2. Punteros de avance para DFS (work pointer para garantizar O(V²E))
        ptr: Dict[str, int] = {n: 0 for n in red.nodos}

        def dfs_bloqueo(u: str, push: float) -> float:
            if u == sumidero or push <= 1e-9:
                return push

            while ptr[u] < len(red.adj[u]):
                arista = red.adj[u][ptr[u]]
                v = arista.v

                if niveles.get(v) == niveles[u] + 1 and arista.residual > 1e-9:
                    empuje = min(push, arista.residual)
                    flujo_enviado = dfs_bloqueo(v, empuje)
                    if flujo_enviado > 1e-9:
                        arista.flujo += flujo_enviado
                        red.adj[v][arista.inversa_idx].flujo -= flujo_enviado
                        return flujo_enviado

                ptr[u] += 1

            return 0.0

        while True:
            enviado = dfs_bloqueo(fuente, float("inf"))
            if enviado <= 1e-9:
                break
            flujo_total += enviado

    return _extraer_corte_y_metricas(red, fuente, sumidero, flujo_total)


def edmonds_karp_flujo_maximo(
    red: RedResidual,
    fuente: str,
    sumidero: str,
) -> ResultadoFlujo:
    """
    Algoritmo de Edmonds-Karp implementado desde cero.
    Encuentra caminos aumentantes más cortos mediante BFS en O(V E²).
    """
    flujo_total = 0.0

    while True:
        padres: Dict[str, Tuple[str, AristaResidual]] = {}
        cola = deque([fuente])

        while cola and sumidero not in padres:
            u = cola.popleft()
            for arista in red.adj[u]:
                if arista.residual > 1e-9 and arista.v not in padres and arista.v != fuente:
                    padres[arista.v] = (u, arista)
                    cola.append(arista.v)

        if sumidero not in padres:
            break

        # Calcular cuello de botella del camino
        cuello = float("inf")
        curr = sumidero
        while curr != fuente:
            u, arista = padres[curr]
            cuello = min(cuello, arista.residual)
            curr = u

        # Aumentar flujo a lo largo del camino
        curr = sumidero
        while curr != fuente:
            u, arista = padres[curr]
            arista.flujo += cuello
            red.adj[arista.v][arista.inversa_idx].flujo -= cuello
            curr = u

        flujo_total += cuello

    return _extraer_corte_y_metricas(red, fuente, sumidero, flujo_total)


def ford_fulkerson_dfs(
    red: RedResidual,
    fuente: str,
    sumidero: str,
) -> ResultadoFlujo:
    """
    Algoritmo clásico de Ford-Fulkerson con búsqueda de caminos por DFS estándar.
    Complejidad: O(E * f) donde f es el flujo máximo.
    """
    flujo_total = 0.0

    def buscar_camino_dfs(u: str, min_cap: float, visitados: Set[str]) -> float:
        if u == sumidero:
            return min_cap
        visitados.add(u)

        for arista in red.adj[u]:
            if arista.residual > 1e-9 and arista.v not in visitados:
                empuje = min(min_cap, arista.residual)
                enviado = buscar_camino_dfs(arista.v, empuje, visitados)
                if enviado > 1e-9:
                    arista.flujo += enviado
                    red.adj[arista.v][arista.inversa_idx].flujo -= enviado
                    return enviado
        return 0.0

    while True:
        visitados: Set[str] = set()
        enviado = buscar_camino_dfs(fuente, float("inf"), visitados)
        if enviado <= 1e-9:
            break
        flujo_total += enviado

    return _extraer_corte_y_metricas(red, fuente, sumidero, flujo_total)
