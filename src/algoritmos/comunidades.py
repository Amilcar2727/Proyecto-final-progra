"""
Algoritmos puros de detección de comunidades en grafos financieros:
1. Louvain (optimización heurística de modularidad en dos fases) con soporte multi-semilla.
2. Componentes conexas por umbral de peso (variante BFS y variante incremental con Union-Find).
3. Propagación de etiquetas ponderada (Label Propagation Algorithm - LPA).
4. Función universal independiente de cálculo de modularidad Q.

Complejidades teóricas:
- Modularidad: O(V + E)
- Louvain: O(E log V) empírico, O(V + E) espacio.
- Componentes por umbral: O(V + E) con BFS, O(E α(V)) con Union-Find.
- LPA: O(k * E) donde k es el número de rondas (típicamente k ≤ 15).
"""

from __future__ import annotations
import math
import random
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.algoritmos.union_find import UnionFind
from src.graph import Edge, Graph


def calcular_modularidad(
    grafo: Graph,
    particion: Dict[str, int],
    gamma: float = 1.0,
    peso_fn: Optional[Callable[[Edge], float]] = None,
) -> float:
    """
    Calcula la modularidad de Newman-Girvan generalizada con parámetro de resolución γ.

    Q = (1 / 2m) * Σ_{ij} [ A_ij - γ * (k_i * k_j) / (2m) ] * δ(c_i, c_j)

    Donde:
    - m = 1/2 * Σ_i k_i (peso total de aristas en el grafo no dirigido)
    - k_i = grado ponderado (fuerza) del nodo i
    - δ(c_i, c_j) = 1 si pertenecen a la misma comunidad, 0 si no.

    Complejidad: O(V + E) tiempo, O(V) espacio.
    """
    if peso_fn is None:
        peso_fn = lambda e: e.monto if e.monto > 0 else float(e.n_transferencias)

    # Construir fuerza ponderada k_i y peso total m
    fuerza: Dict[str, float] = defaultdict(float)
    peso_interno_comunidad: Dict[int, float] = defaultdict(float)
    fuerza_comunidad: Dict[int, float] = defaultdict(float)

    # Recorrer aristas
    m_total = 0.0
    for e in grafo.iter_aristas():
        w = float(peso_fn(e))
        if w <= 0:
            continue
        u, v = e.origen, e.destino
        if u not in particion or v not in particion:
            continue

        fuerza[u] += w
        if u != v:
            fuerza[v] += w
            m_total += w
            c_u = particion[u]
            c_v = particion[v]
            if c_u == c_v:
                peso_interno_comunidad[c_u] += 2.0 * w
        else:
            # Self-loop
            m_total += w
            c_u = particion[u]
            peso_interno_comunidad[c_u] += 2.0 * w

    if m_total <= 0:
        return 0.0

    dos_m = 2.0 * m_total

    for u, c in particion.items():
        fuerza_comunidad[c] += fuerza[u]

    q = 0.0
    for c, sigma_tot in fuerza_comunidad.items():
        sigma_in = peso_interno_comunidad[c]
        q += (sigma_in / dos_m) - gamma * ((sigma_tot / dos_m) ** 2)

    return float(q)


def componentes_por_umbral_bfs(
    grafo: Graph,
    umbral_peso: float,
    peso_fn: Optional[Callable[[Edge], float]] = None,
) -> Dict[str, int]:
    """
    Agrupa nodos en componentes conexas conservando únicamente aristas cuyo peso >= umbral_peso
    utilizando recorrido en anchura (BFS).

    Complejidad: O(V + E) tiempo, O(V) espacio.
    """
    if peso_fn is None:
        peso_fn = lambda e: e.monto if e.monto > 0 else float(e.n_transferencias)

    # Construir lista de adyacencia filtrada
    adj_filtrada: Dict[str, Set[str]] = {n: set() for n in grafo.nodes}
    for e in grafo.iter_aristas():
        if peso_fn(e) >= umbral_peso:
            adj_filtrada[e.origen].add(e.destino)
            adj_filtrada[e.destino].add(e.origen)

    particion: Dict[str, int] = {}
    comunidad_actual = 0
    visitados: Set[str] = set()

    for nodo in grafo.nodes:
        if nodo not in visitados:
            cola = [nodo]
            visitados.add(nodo)
            particion[nodo] = comunidad_actual

            idx = 0
            while idx < len(cola):
                u = cola[idx]
                idx += 1
                for v in adj_filtrada[u]:
                    if v not in visitados:
                        visitados.add(v)
                        particion[v] = comunidad_actual
                        cola.append(v)
            comunidad_actual += 1

    return particion


def componentes_por_umbral_union_find(
    grafo: Graph,
    umbral_peso: float,
    peso_fn: Optional[Callable[[Edge], float]] = None,
) -> Tuple[Dict[str, int], UnionFind[str]]:
    """
    Agrupa nodos en componentes conexas por umbral utilizando Union-Find.
    Permite actualizaciones incrementales ante nuevas transacciones en O(α(V)).

    Complejidad: O(V + E α(V)) tiempo, O(V) espacio.
    """
    if peso_fn is None:
        peso_fn = lambda e: e.monto if e.monto > 0 else float(e.n_transferencias)

    uf = UnionFind(grafo.nodes.keys())
    for e in grafo.iter_aristas():
        if peso_fn(e) >= umbral_peso:
            uf.union(e.origen, e.destino)

    componentes = uf.obtener_componentes()
    particion: Dict[str, int] = {}
    for cid, (raiz, miembros) in enumerate(componentes.items()):
        for m in miembros:
            particion[m] = cid

    return particion, uf


def barrido_umbrales(
    grafo: Graph,
    umbrales: List[float],
    peso_fn: Optional[Callable[[Edge], float]] = None,
) -> List[Dict[str, Any]]:
    """
    Realiza un análisis paramétrico de sensibilidad variando el umbral de peso.
    Retorna tabla con número de comunidades, tamaño promedio y modularidad.
    """
    reporte = []
    for umbral in sorted(umbrales):
        particion = componentes_por_umbral_bfs(grafo, umbral, peso_fn)
        tamanos = defaultdict(int)
        for c in particion.values():
            tamanos[c] += 1
        tam_lista = list(tamanos.values())
        mod = calcular_modularidad(grafo, particion, peso_fn=peso_fn)

        reporte.append({
            "umbral": umbral,
            "num_comunidades": len(tamanos),
            "tamano_maximo": max(tam_lista) if tam_lista else 0,
            "tamano_minimo": min(tam_lista) if tam_lista else 0,
            "tamano_promedio": sum(tam_lista) / len(tam_lista) if tam_lista else 0.0,
            "modularidad": mod,
        })
    return reporte


def propagacion_etiquetas(
    grafo: Graph,
    peso_fn: Optional[Callable[[Edge], float]] = None,
    max_iteraciones: int = 50,
    seed: int = 42,
) -> Dict[str, int]:
    """
    Algoritmo de Propagación de Etiquetas (LPA) ponderado implementado desde cero.
    En cada iteración, cada nodo adopta la etiqueta de la comunidad con mayor peso acumulado
    entre sus vecinos, con orden aleatorio y desempate aleatorio reproducible.

    Complejidad: O(k * E) donde k ≤ max_iteraciones, espacio O(V + E).
    """
    rng = random.Random(seed)
    if peso_fn is None:
        peso_fn = lambda e: e.monto if e.monto > 0 else float(e.n_transferencias)

    # Construir adyacencia no dirigida ponderada
    vecinos_peso: Dict[str, Dict[str, float]] = {n: defaultdict(float) for n in grafo.nodes}
    for e in grafo.iter_aristas():
        w = float(peso_fn(e))
        if w > 0:
            vecinos_peso[e.origen][e.destino] += w
            if e.origen != e.destino:
                vecinos_peso[e.destino][e.origen] += w

    # Inicializar cada nodo con su propia etiqueta
    nodos = list(grafo.nodes.keys())
    etiquetas: Dict[str, int] = {nodo: idx for idx, nodo in enumerate(nodos)}

    for _ in range(max_iteraciones):
        cambios = 0
        rng.shuffle(nodos)
        for u in nodos:
            vecinos = vecinos_peso[u]
            if not vecinos:
                continue

            pesos_por_etiqueta: Dict[int, float] = defaultdict(float)
            for v, w in vecinos.items():
                pesos_por_etiqueta[etiquetas[v]] += w

            # Encontrar etiquetas con peso máximo
            max_w = max(pesos_por_etiqueta.values())
            candidatas = [etq for etq, w in pesos_por_etiqueta.items() if math.isclose(w, max_w, rel_tol=1e-9)]
            nueva_etiqueta = rng.choice(candidatas)

            if nueva_etiqueta != etiquetas[u]:
                etiquetas[u] = nueva_etiqueta
                cambios += 1

        if cambios == 0:
            break

    # Normalizar etiquetas consecutivas 0, 1, 2...
    mapeo_normalizado: Dict[int, int] = {}
    particion_final: Dict[str, int] = {}
    for nodo, etq in etiquetas.items():
        if etq not in mapeo_normalizado:
            mapeo_normalizado[etq] = len(mapeo_normalizado)
        particion_final[nodo] = mapeo_normalizado[etq]

    return particion_final


class AlgoritmoLouvain:
    """
    Implementación completa y desde cero del algoritmo Louvain (Blondel et al., 2008)
    para optimización heurística de modularidad en grafos ponderados.

    Incluye:
    - Fase 1: Movimientos locales ávidos guiados por ΔQ incremental en O(1) por vecino.
    - Fase 2: Agregación de comunidades en supernodos y contracción de red.
    - Jerarquía de niveles y selección multi-semilla con reporte de estabilidad.

    Complejidad:
    - Temporal: O(E log V) empírico.
    - Espacial: O(V + E).
    """

    def __init__(
        self,
        gamma: float = 1.0,
        tolerancia: float = 1e-7,
        max_fases: int = 20,
    ) -> None:
        self.gamma = gamma
        self.tolerancia = tolerancia
        self.max_fases = max_fases

    def ejecutar_una_corrida(
        self,
        grafo: Graph,
        peso_fn: Optional[Callable[[Edge], float]] = None,
        seed: int = 42,
    ) -> Tuple[Dict[str, int], float, List[Dict[str, int]]]:
        """
        Ejecuta el ciclo de dos fases de Louvain con una semilla fija.

        Retorna:
            - particion: mapeo final {id_nodo: id_comunidad}
            - modularidad_final: valor Q obtenido
            - jerarquia_niveles: lista de particiones en cada nivel de agregación
        """
        rng = random.Random(seed)
        if peso_fn is None:
            peso_fn = lambda e: e.monto if e.monto > 0 else float(e.n_transferencias)

        # 1. Extraer matriz de adyacencia compacta y pesada
        nodos_originales = list(grafo.nodes.keys())
        if not nodos_originales:
            return {}, 0.0, []

        # Representación interna: adyacencia {u: {v: peso}} y auto-lazos {u: peso}
        adj_actual: Dict[str, Dict[str, float]] = {u: defaultdict(float) for u in nodos_originales}
        self_loops: Dict[str, float] = {u: 0.0 for u in nodos_originales}

        for e in grafo.iter_aristas():
            w = float(peso_fn(e))
            if w <= 0:
                continue
            u, v = e.origen, e.destino
            if u == v:
                self_loops[u] += w
            else:
                adj_actual[u][v] += w
                adj_actual[v][u] += w

        m_total = sum(self_loops.values()) + sum(
            w for u in adj_actual for v, w in adj_actual[u].items() if u < v
        )
        if m_total <= 0:
            return {u: 0 for u in nodos_originales}, 0.0, []

        dos_m = 2.0 * m_total

        # Mapeo de nodos originales a supernodos actuales
        particion_global: Dict[str, str] = {u: u for u in nodos_originales}
        jerarquia: List[Dict[str, int]] = []

        q_actual = self._calcular_q_interno(adj_actual, self_loops, {u: u for u in adj_actual}, dos_m)

        for _ in range(self.max_fases):
            # Fase 1: optimización local
            particion_nivel, mejora_fase1 = self._fase1_optimizacion_local(
                adj_actual, self_loops, dos_m, rng
            )

            # Actualizar particion global
            nueva_particion_global: Dict[str, str] = {}
            for orig_node, supernodo in particion_global.items():
                nueva_particion_global[orig_node] = particion_nivel[supernodo]
            particion_global = nueva_particion_global

            # Guardar snapshot de jerarquía normalizado
            map_norm: Dict[str, int] = {}
            snapshot: Dict[str, int] = {}
            for k, v in particion_global.items():
                if v not in map_norm:
                    map_norm[v] = len(map_norm)
                snapshot[k] = map_norm[v]
            jerarquia.append(snapshot)

            q_nuevo = calcular_modularidad(grafo, snapshot, gamma=self.gamma, peso_fn=peso_fn)

            if q_nuevo - q_actual <= self.tolerancia or len(set(particion_nivel.values())) == len(adj_actual):
                q_actual = q_nuevo
                break

            q_actual = q_nuevo

            # Fase 2: Agregación en supernodos
            adj_actual, self_loops = self._fase2_agregacion(adj_actual, self_loops, particion_nivel)

        # Normalizar partición final a enteros 0..C-1
        mapeo_final: Dict[str, int] = {}
        particion_resultado: Dict[str, int] = {}
        for nodo, c in particion_global.items():
            if c not in mapeo_final:
                mapeo_final[c] = len(mapeo_final)
            particion_resultado[nodo] = mapeo_final[c]

        q_final = calcular_modularidad(grafo, particion_resultado, gamma=self.gamma, peso_fn=peso_fn)
        return particion_resultado, q_final, jerarquia

    def _fase1_optimizacion_local(
        self,
        adj: Dict[str, Dict[str, float]],
        self_loops: Dict[str, float],
        dos_m: float,
        rng: random.Random,
    ) -> Tuple[Dict[str, str], bool]:
        """
        Mueve iterativamente cada nodo a la comunidad de un vecino que maximice ΔQ.
        """
        # Calcular fuerza k_i de cada nodo
        k_i: Dict[str, float] = {}
        for u in adj:
            k_i[u] = 2.0 * self_loops[u] + sum(adj[u].values())

        # Inicialmente cada nodo en su propia comunidad
        comunidad: Dict[str, str] = {u: u for u in adj}
        sigma_tot: Dict[str, float] = {u: k_i[u] for u in adj}
        sigma_in: Dict[str, float] = {u: 2.0 * self_loops[u] for u in adj}

        nodos = list(adj.keys())
        mejora_global = False

        while True:
            mejora_pasada = False
            rng.shuffle(nodos)

            for u in nodos:
                c_u = comunidad[u]
                k_u = k_i[u]

                # Aristas incidentes a comunidades vecinas
                k_i_in_por_c: Dict[str, float] = defaultdict(float)
                for v, w in adj[u].items():
                    c_v = comunidad[v]
                    k_i_in_por_c[c_v] += w

                # Remover u de su comunidad c_u
                # Se descuenta la interacción con la propia comunidad c_u
                k_u_cu = k_i_in_por_c.get(c_u, 0.0)
                sigma_tot[c_u] -= k_u
                sigma_in[c_u] -= (2.0 * k_u_cu + 2.0 * self_loops[u])

                mejor_comunidad = c_u
                mejor_delta_q = 0.0

                # Evaluar ganancia modular al mover u a cada comunidad vecina candidata
                candidatas = set(k_i_in_por_c.keys())
                candidatas.add(c_u)

                for c_cand in candidatas:
                    k_i_in = k_i_in_por_c.get(c_cand, 0.0)
                    s_tot = sigma_tot[c_cand]
                    # ΔQ = (k_i_in / 2m) - γ * (k_u * s_tot / (2m)^2)
                    delta_q = (k_i_in / dos_m) - self.gamma * ((k_u * s_tot) / (dos_m ** 2))

                    if delta_q > mejor_delta_q + self.tolerancia:
                        mejor_delta_q = delta_q
                        mejor_comunidad = c_cand

                # Insertar u en la mejor comunidad encontrada
                comunidad[u] = mejor_comunidad
                k_u_nueva = k_i_in_por_c.get(mejor_comunidad, 0.0)
                sigma_tot[mejor_comunidad] += k_u
                sigma_in[mejor_comunidad] += (2.0 * k_u_nueva + 2.0 * self_loops[u])

                if mejor_comunidad != c_u:
                    mejora_pasada = True
                    mejora_global = True

            if not mejora_pasada:
                break

        return comunidad, mejora_global

    def _fase2_agregacion(
        self,
        adj: Dict[str, Dict[str, float]],
        self_loops: Dict[str, float],
        particion: Dict[str, str],
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
        """
        Contrae comunidades en supernodos.
        """
        supernodos = sorted(list(set(particion.values())))
        nueva_adj: Dict[str, Dict[str, float]] = {c: defaultdict(float) for c in supernodos}
        nuevos_loops: Dict[str, float] = {c: 0.0 for c in supernodos}

        # Transferir self-loops existentes
        for u, loop_w in self_loops.items():
            nuevos_loops[particion[u]] += loop_w

        # Transferir aristas
        for u in adj:
            c_u = particion[u]
            for v, w in adj[u].items():
                c_v = particion[v]
                if c_u == c_v:
                    # En la contracción, aristas internas u-v se acumulan como lazo
                    if u < v:
                        nuevos_loops[c_u] += w
                else:
                    nueva_adj[c_u][c_v] += w

        return nueva_adj, nuevos_loops

    def _calcular_q_interno(
        self,
        adj: Dict[str, Dict[str, float]],
        self_loops: Dict[str, float],
        particion: Dict[str, str],
        dos_m: float,
    ) -> float:
        """Calcula modularidad sobre la representación interna condensada."""
        sigma_tot: Dict[str, float] = defaultdict(float)
        sigma_in: Dict[str, float] = defaultdict(float)

        for u in adj:
            c_u = particion[u]
            deg = 2.0 * self_loops[u] + sum(adj[u].values())
            sigma_tot[c_u] += deg
            sigma_in[c_u] += 2.0 * self_loops[u]
            for v, w in adj[u].items():
                if particion[v] == c_u:
                    sigma_in[c_u] += w

        q = 0.0
        for c in sigma_tot:
            q += (sigma_in[c] / dos_m) - self.gamma * ((sigma_tot[c] / dos_m) ** 2)
        return float(q)

    def ejecutar_multi_semilla(
        self,
        grafo: Graph,
        n_corridas: int = 5,
        semilla_base: int = 42,
        peso_fn: Optional[Callable[[Edge], float]] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta Louvain con múltiples semillas para mitigar óptimos locales
        y reporta la mejor partición junto con una métrica de estabilidad.
        """
        mejor_particion: Dict[str, int] = {}
        mejor_q = -float("inf")
        mejor_jerarquia: List[Dict[str, int]] = []
        todas_particiones: List[Dict[str, int]] = []

        for i in range(n_corridas):
            seed = semilla_base + i * 17
            part, q, jerarquia = self.ejecutar_una_corrida(grafo, peso_fn=peso_fn, seed=seed)
            todas_particiones.append(part)
            if q > mejor_q:
                mejor_q = q
                mejor_particion = part
                mejor_jerarquia = jerarquia

        # Medir estabilidad: porcentaje de coincidencia de pares de nodos
        nodos = list(mejor_particion.keys())
        estabilidad = 1.0
        if len(nodos) > 1 and len(todas_particiones) > 1:
            # Tomar muestra de pares si la red es grande para mantener eficiencia
            pares = []
            for idx_a in range(min(len(nodos), 100)):
                for idx_b in range(idx_a + 1, min(len(nodos), 100)):
                    pares.append((nodos[idx_a], nodos[idx_b]))

            acuerdos = 0
            total_evaluaciones = 0
            for u, v in pares:
                # Verificar si u y v siempre quedan juntos o siempre separados
                estados = [p.get(u) == p.get(v) for p in todas_particiones]
                if all(estados) or not any(estados):
                    acuerdos += 1
                total_evaluaciones += 1
            estabilidad = acuerdos / total_evaluaciones if total_evaluaciones > 0 else 1.0

        return {
            "particion": mejor_particion,
            "modularidad": mejor_q,
            "jerarquia": mejor_jerarquia,
            "estabilidad": estabilidad,
            "n_corridas": n_corridas,
        }
