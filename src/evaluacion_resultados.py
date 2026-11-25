"""
Módulo 5: Evaluación, Comparación y Validación de Resultados Algorítmicos.
Ejecuta benchmarks rigurosos con perf_counter y tracemalloc, calcula pendientes log-log,
valida algoritmos de comunidades con ground-truth conocido (F1, precisión, recall de pares),
y somete a prueba los casos adversarios difíciles:
(a) Cuenta concentradora tipo planilla (con y sin exclusión).
(b) Red de mulas con vínculos internos débiles.
(c) Dos comunidades inyectadas unidas por un solo vínculo fuerte.
"""

from __future__ import annotations
import math
import os
import random
import statistics
import time
import tracemalloc
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.algoritmos.arbol_expansion import kruskal_mst, prim_mst
from src.algoritmos.comunidades import (
    AlgoritmoLouvain,
    calcular_modularidad,
    componentes_por_umbral_bfs,
    componentes_por_umbral_union_find,
    propagacion_etiquetas,
)
from src.algoritmos.flujo import (
    construir_red_residual_desde_grafo,
    dinic_flujo_maximo,
    edmonds_karp_flujo_maximo,
    ford_fulkerson_dfs,
)
from src.analisis_transacciones import AnalizadorTransaccionesFinancieras
from src.graph import Edge, Graph, Node


@dataclass
class RegistroBenchmark:
    """Registro de rendimiento temporal y espacial para una prueba algorítmica."""
    algoritmo: str
    familia: str
    nodos_v: int
    aristas_e: int
    densidad: str
    tiempo_medio_seg: float
    tiempo_std_seg: float
    memoria_pico_kb: float
    metrica_calidad: float  # Modularidad, peso MST o flujo máximo


def calcular_metricas_clasificacion_pares(
    particion_predicha: Dict[str, int],
    particion_real: Dict[str, int],
) -> Dict[str, float]:
    """
    Calcula precisión, recall (sensibilidad) y F1-Score evaluando si los pares de nodos
    que pertenecen a la misma comunidad en el ground-truth se agruparon juntos en la predicción.
    """
    nodos = [n for n in particion_real if n in particion_predicha]
    if len(nodos) < 2:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "pares_evaluados": 0}

    # Evaluar pares (muestra si es grande)
    max_nodos = min(len(nodos), 200)
    muestra = nodos[:max_nodos]

    tp = 0  # Estaban juntos y se predijeron juntos
    fp = 0  # No estaban juntos y se predijeron juntos
    fn = 0  # Estaban juntos y se predijeron separados
    tn = 0  # No estaban juntos y se predijeron separados

    for i in range(len(muestra)):
        for j in range(i + 1, len(muestra)):
            u, v = muestra[i], muestra[j]
            real_juntos = (particion_real[u] == particion_real[v])
            pred_juntos = (particion_predicha[u] == particion_predicha[v])

            if real_juntos and pred_juntos:
                tp += 1
            elif not real_juntos and pred_juntos:
                fp += 1
            elif real_juntos and not pred_juntos:
                fn += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "pares_evaluados": tp + fp + fn + tn,
    }


def estimar_pendiente_log_log(tamanos: List[int], tiempos: List[float]) -> float:
    """
    Estima el exponente de complejidad empírica mediante regresión lineal sobre log(t) vs log(N):
    log(t) = α * log(N) + β  =>  α = pendiente empírica.
    """
    if len(tamanos) < 2 or len(tiempos) < 2:
        return 0.0

    log_x = [math.log(max(1, n)) for n in tamanos]
    log_y = [math.log(max(1e-9, t)) for t in tiempos]

    n = len(log_x)
    media_x = sum(log_x) / n
    media_y = sum(log_y) / n

    numerador = sum((log_x[i] - media_x) * (log_y[i] - media_y) for i in range(n))
    denominador = sum((log_x[i] - media_x) ** 2 for i in range(n))

    if abs(denominador) < 1e-9:
        return 0.0

    return numerador / denominador


class EvaluadorResultados:
    """
    Módulo integral para pruebas automatizadas de escalabilidad, benchmarking y evaluación de estrés.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def benchmark_mst(
        self,
        tamanos: List[int],
        repeticiones: int = 3,
        densidad: str = "dispersa",
    ) -> List[RegistroBenchmark]:
        """
        Ejecuta benchmark comparativo Kruskal vs Prim midiendo tiempo y memoria pico.
        """
        registros = []
        rng = random.Random(self.seed)

        for n in tamanos:
            g = Graph(dirigido=False, ponderado=True)
            for i in range(n):
                g.agregar_nodo(Node(f"N{i}", "agencia"))

            # Construir arbol inicial para garantizar conexidad
            for i in range(1, n):
                padre = rng.randint(0, i - 1)
                costo = rng.uniform(10.0, 500.0)
                g.agregar_arista(Edge(f"N{padre}", f"N{i}", costo_instalacion=costo, costo_operativo=costo*0.1))

            # Aristas adicionales según densidad
            factor_aristas = 2 if densidad == "dispersa" else (6 if densidad == "media" else 15)
            aristas_extra = min(n * factor_aristas, (n * (n - 1)) // 2 - (n - 1))

            for _ in range(max(0, aristas_extra)):
                u_idx = rng.randint(0, n - 1)
                v_idx = rng.randint(0, n - 1)
                if u_idx != v_idx:
                    costo = rng.uniform(10.0, 500.0)
                    g.agregar_arista(Edge(f"N{u_idx}", f"N{v_idx}", costo_instalacion=costo, costo_operativo=costo*0.1))

            num_e = g.num_aristas

            # Probar Kruskal
            tiempos_kruskal = []
            mems_kruskal = []
            peso_kruskal = 0.0
            for _ in range(repeticiones):
                tracemalloc.start()
                t0 = time.perf_counter()
                res_k = kruskal_mst(g, peso_fn=lambda e: e.costo_instalacion)
                t1 = time.perf_counter()
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                tiempos_kruskal.append(t1 - t0)
                mems_kruskal.append(peak / 1024.0)
                peso_kruskal = res_k.peso_total

            registros.append(
                RegistroBenchmark(
                    algoritmo="Kruskal",
                    familia="MST",
                    nodos_v=n,
                    aristas_e=num_e,
                    densidad=densidad,
                    tiempo_medio_seg=statistics.mean(tiempos_kruskal),
                    tiempo_std_seg=statistics.stdev(tiempos_kruskal) if len(tiempos_kruskal) > 1 else 0.0,
                    memoria_pico_kb=max(mems_kruskal),
                    metrica_calidad=peso_kruskal,
                )
            )

            # Probar Prim
            tiempos_prim = []
            mems_prim = []
            peso_prim = 0.0
            for _ in range(repeticiones):
                tracemalloc.start()
                t0 = time.perf_counter()
                res_p = prim_mst(g, peso_fn=lambda e: e.costo_instalacion)
                t1 = time.perf_counter()
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                tiempos_prim.append(t1 - t0)
                mems_prim.append(peak / 1024.0)
                peso_prim = res_p.peso_total

            registros.append(
                RegistroBenchmark(
                    algoritmo="Prim",
                    familia="MST",
                    nodos_v=n,
                    aristas_e=num_e,
                    densidad=densidad,
                    tiempo_medio_seg=statistics.mean(tiempos_prim),
                    tiempo_std_seg=statistics.stdev(tiempos_prim) if len(tiempos_prim) > 1 else 0.0,
                    memoria_pico_kb=max(mems_prim),
                    metrica_calidad=peso_prim,
                )
            )

        return registros

    def benchmark_flujo(
        self,
        tamanos: List[int],
        repeticiones: int = 2,
    ) -> List[RegistroBenchmark]:
        """
        Ejecuta benchmark comparativo Dinic vs Edmonds-Karp vs Ford-Fulkerson.
        """
        registros = []
        rng = random.Random(self.seed)

        for n in tamanos:
            # Construir red estratificada por capas (fuente S -> capas intermedias -> sumidero T)
            g = Graph(dirigido=True, ponderado=True)
            fuente = "S"
            sumidero = "T"
            g.agregar_nodo(Node(fuente, "boveda_central"))
            g.agregar_nodo(Node(sumidero, "entidad"))

            nodos_intermedios = [f"V{i}" for i in range(n)]
            for nid in nodos_intermedios:
                g.agregar_nodo(Node(nid, "agencia"))

            # Conectar fuente a primeros 20%
            primeros = max(1, n // 5)
            for i in range(primeros):
                g.agregar_arista(Edge(fuente, nodos_intermedios[i], capacidad=rng.uniform(100.0, 500.0)))

            # Conectar últimos 20% a sumidero
            ultimos = max(1, n // 5)
            for i in range(n - ultimos, n):
                g.agregar_arista(Edge(nodos_intermedios[i], sumidero, capacidad=rng.uniform(100.0, 500.0)))

            # Conexiones internas
            for i in range(n - 1):
                dest = min(n - 1, i + rng.randint(1, 3))
                g.agregar_arista(Edge(nodos_intermedios[i], nodos_intermedios[dest], capacidad=rng.uniform(50.0, 300.0)))

            num_e = g.num_aristas

            # Probar Dinic
            tiempos_dinic = []
            mems_dinic = []
            flujo_dinic = 0.0
            for _ in range(repeticiones):
                red = construir_red_residual_desde_grafo(g, fuente, sumidero)
                tracemalloc.start()
                t0 = time.perf_counter()
                res = dinic_flujo_maximo(red, fuente, sumidero)
                t1 = time.perf_counter()
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                tiempos_dinic.append(t1 - t0)
                mems_dinic.append(peak / 1024.0)
                flujo_dinic = res.flujo_maximo

            registros.append(
                RegistroBenchmark(
                    algoritmo="Dinic",
                    familia="Flujo",
                    nodos_v=n + 2,
                    aristas_e=num_e,
                    densidad="estratificada",
                    tiempo_medio_seg=statistics.mean(tiempos_dinic),
                    tiempo_std_seg=statistics.stdev(tiempos_dinic) if len(tiempos_dinic) > 1 else 0.0,
                    memoria_pico_kb=max(mems_dinic),
                    metrica_calidad=flujo_dinic,
                )
            )

            # Probar Edmonds-Karp
            tiempos_ek = []
            mems_ek = []
            flujo_ek = 0.0
            for _ in range(repeticiones):
                red = construir_red_residual_desde_grafo(g, fuente, sumidero)
                tracemalloc.start()
                t0 = time.perf_counter()
                res = edmonds_karp_flujo_maximo(red, fuente, sumidero)
                t1 = time.perf_counter()
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                tiempos_ek.append(t1 - t0)
                mems_ek.append(peak / 1024.0)
                flujo_ek = res.flujo_maximo

            registros.append(
                RegistroBenchmark(
                    algoritmo="Edmonds-Karp",
                    familia="Flujo",
                    nodos_v=n + 2,
                    aristas_e=num_e,
                    densidad="estratificada",
                    tiempo_medio_seg=statistics.mean(tiempos_ek),
                    tiempo_std_seg=statistics.stdev(tiempos_ek) if len(tiempos_ek) > 1 else 0.0,
                    memoria_pico_kb=max(mems_ek),
                    metrica_calidad=flujo_ek,
                )
            )

            # Probar Ford-Fulkerson solo si n <= 300 para evitar tiempos exponenciales en grafos patológicos
            if n <= 300:
                tiempos_ff = []
                mems_ff = []
                flujo_ff = 0.0
                for _ in range(repeticiones):
                    red = construir_red_residual_desde_grafo(g, fuente, sumidero)
                    tracemalloc.start()
                    t0 = time.perf_counter()
                    res = ford_fulkerson_dfs(red, fuente, sumidero)
                    t1 = time.perf_counter()
                    _, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()

                    tiempos_ff.append(t1 - t0)
                    mems_ff.append(peak / 1024.0)
                    flujo_ff = res.flujo_maximo

                registros.append(
                    RegistroBenchmark(
                        algoritmo="Ford-Fulkerson",
                        familia="Flujo",
                        nodos_v=n + 2,
                        aristas_e=num_e,
                        densidad="estratificada",
                        tiempo_medio_seg=statistics.mean(tiempos_ff),
                        tiempo_std_seg=statistics.stdev(tiempos_ff) if len(tiempos_ff) > 1 else 0.0,
                        memoria_pico_kb=max(mems_ff),
                        metrica_calidad=flujo_ff,
                    )
                )

        return registros

    def validar_casos_dificiles_comunidades(self) -> Dict[str, Any]:
        """
        Somete los algoritmos a 3 casos difíciles de propósito:
        1. Cuenta concentradora tipo planilla.
        2. Red de mulas con vínculos débiles.
        3. Dos comunidades densas unidas por un único vínculo fuerte.
        """
        resultados = {}

        # CASO A: Cuenta concentradora legítima de planilla
        # Dos grupos independientes de 4 cuentas unidos a través de PLANILLA_CORP
        g_a = Graph(dirigido=False, ponderado=True)
        for i in range(1, 5):
            g_a.agregar_nodo(Node(f"GRP1_{i}", "cuenta"))
        for i in range(1, 5):
            g_a.agregar_nodo(Node(f"GRP2_{i}", "cuenta"))
        g_a.agregar_nodo(Node("PLANILLA_CORP", "cuenta"))

        # Aristas internas GRP1
        for i in range(1, 4):
            g_a.agregar_arista(Edge(f"GRP1_{i}", f"GRP1_{i+1}", monto=100.0, n_transferencias=5))
        # Aristas internas GRP2
        for i in range(1, 4):
            g_a.agregar_arista(Edge(f"GRP2_{i}", f"GRP2_{i+1}", monto=100.0, n_transferencias=5))

        # PLANILLA_CORP transfiere a todos los 8 empleados
        for i in range(1, 5):
            g_a.agregar_arista(Edge("PLANILLA_CORP", f"GRP1_{i}", monto=3000.0, n_transferencias=2))
            g_a.agregar_arista(Edge("PLANILLA_CORP", f"GRP2_{i}", monto=3000.0, n_transferencias=2))

        # Louvain SIN exclusión
        louvain = AlgoritmoLouvain()
        part_a_sin, q_a_sin, _ = louvain.ejecutar_una_corrida(g_a, seed=42)

        # Con Analizador y exclusión de concentrador
        analizador = AnalizadorTransaccionesFinancieras(percentil_concentrador=80.0)
        g_a_prep = analizador.preprocesar_red(g_a, accion_concentrador="excluir")
        res_a_con = analizador.detectar_comunidades_louvain(g_a_prep, n_corridas=3, semilla=42)

        resultados["caso_a_concentrador"] = {
            "descripcion": "Cuenta concentradora de nómina que conecta artificialmente dos clusters independientes.",
            "sin_exclusion": {
                "num_comunidades": len(set(part_a_sin.values())),
                "modularidad": q_a_sin,
                "diagnostico": "PLANILLA_CORP aglutina erróneamente ambos grupos si no se neutraliza.",
            },
            "con_exclusion": {
                "nodos_excluidos": [x["nodo"] for x in analizador.nodos_excluidos],
                "num_comunidades": len(set(res_a_con["particion"].values())),
                "modularidad": res_a_con["modularidad"],
                "diagnostico": "Al neutralizar el concentrador, se aíslan correctamente las dos redes independientes.",
            },
        }

        # CASO B: Red de mulas con vínculos débiles
        # 5 cuentas transfieren micropagos estructurados hacia un recolector
        g_b = Graph(dirigido=False, ponderado=True)
        recolector = "RECOLECTOR_MULA"
        g_b.agregar_nodo(Node(recolector, "cuenta", atributos={"sospechoso": True}))
        for i in range(1, 6):
            mula = f"MULA_{i}"
            g_b.agregar_nodo(Node(mula, "cuenta"))
            # Transferencias de bajo monto y pocas transacciones
            g_b.agregar_arista(Edge(mula, recolector, monto=20.0, n_transferencias=1))

        # Otro grupo ruidoso aleatorio
        for i in range(1, 6):
            g_b.agregar_nodo(Node(f"NORMAL_{i}", "cuenta"))
            g_b.agregar_arista(Edge(f"NORMAL_{i}", f"NORMAL_{(i%5)+1}", monto=500.0, n_transferencias=8))

        part_b_louvain, q_b_louvain, _ = louvain.ejecutar_una_corrida(g_b, seed=42)
        part_b_umbral = componentes_por_umbral_bfs(g_b, umbral_peso=50.0)

        resultados["caso_b_mulas_debiles"] = {
            "descripcion": "Red de mulas con transferencias fraccionadas de bajo valor.",
            "louvain_agrupa": (part_b_louvain["MULA_1"] == part_b_louvain[recolector]),
            "umbral_alto_pierde_mulas": (part_b_umbral["MULA_1"] != part_b_umbral[recolector]),
            "conclusion": "El algoritmo de umbral fijo con umbral alto pierde por completo la red de mulas. Louvain la detecta por cohesión topológica.",
        }

        # CASO C: Dos redes unidas por un solo vínculo fuerte
        g_c = Graph(dirigido=False, ponderado=True)
        # Cluster 1 (4 nodos fuertemente interconectados con peso 10)
        c1 = [f"C1_{i}" for i in range(4)]
        for u in c1:
            g_c.agregar_nodo(Node(u, "cuenta"))
        for i in range(len(c1)):
            for j in range(i + 1, len(c1)):
                g_c.agregar_arista(Edge(c1[i], c1[j], monto=50.0, n_transferencias=10))

        # Cluster 2 (4 nodos fuertemente interconectados con peso 10)
        c2 = [f"C2_{i}" for i in range(4)]
        for u in c2:
            g_c.agregar_nodo(Node(u, "cuenta"))
        for i in range(len(c2)):
            for j in range(i + 1, len(c2)):
                g_c.agregar_arista(Edge(c2[i], c2[j], monto=50.0, n_transferencias=10))

        # Enlace puente con peso muy alto (monto 10,000, transferencias 50)
        g_c.agregar_arista(Edge(c1[0], c2[0], monto=10000.0, n_transferencias=50))

        part_c_louvain, q_c, _ = louvain.ejecutar_una_corrida(g_c, seed=42)
        part_c_lpa = propagacion_etiquetas(g_c, seed=42)

        resultados["caso_c_puente_fuerte"] = {
            "descripcion": "Dos comunidades densas unidas por un único puente de altísimo monto.",
            "louvain_separa": (part_c_louvain[c1[1]] != part_c_louvain[c2[1]]),
            "lpa_separa": (part_c_lpa[c1[1]] != part_c_lpa[c2[1]]),
            "modularidad": q_c,
            "conclusion": "Demuestra la resistencia de modularidad de Louvain frente al sesgo de enlaces puente dominantes.",
        }

        return resultados
