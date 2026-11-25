"""
Módulo de generación de gráficas de complejidad algorítmica para OptiFin.
Produce y guarda en reports/ los siguientes gráficos:
  1. Complejidad teórica de los 10 algoritmos (curvas analíticas).
  2. Benchmark empírico MST (Kruskal vs Prim) con pendiente log-log.
  3. Benchmark empírico Flujo Máximo (Dinic vs Edmonds-Karp vs Ford-Fulkerson).
  4. Comparación modularidad: Louvain vs LPA vs Umbral en función de V.
  5. Uso de memoria pico por algoritmo y tamaño.
Uso:
    python scripts/graficar_complejidad.py
"""

from __future__ import annotations
import math
import os
import random
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from src.algoritmos.arbol_expansion import kruskal_mst, prim_mst
from src.algoritmos.comunidades import (
    AlgoritmoLouvain,
    calcular_modularidad,
    componentes_por_umbral_bfs,
    propagacion_etiquetas,
)
from src.algoritmos.flujo import (
    construir_red_residual_desde_grafo,
    dinic_flujo_maximo,
    edmonds_karp_flujo_maximo,
    ford_fulkerson_dfs,
)
from src.evaluacion_resultados import estimar_pendiente_log_log
from src.graph import Edge, Graph, Node

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

COLORES = {
    "Kruskal":        "#2196F3",
    "Prim":           "#FF9800",
    "Dinic":          "#4CAF50",
    "Edmonds-Karp":   "#9C27B0",
    "Ford-Fulkerson": "#F44336",
    "Louvain":        "#00BCD4",
    "LPA":            "#FF5722",
    "Umbral":         "#607D8B",
}

RNG = random.Random(42)


# ─────────────────────────────────────────────────────────────────────────────
# Generadores de redes sintéticas
# ─────────────────────────────────────────────────────────────────────────────

def _grafo_esparso(n: int, dirigido: bool = False) -> Graph:
    g = Graph(dirigido=dirigido, ponderado=True)
    for i in range(n):
        g.agregar_nodo(Node(f"N{i}", "cuenta"))
    for i in range(1, n):
        p = RNG.randint(0, i - 1)
        c = RNG.uniform(1.0, 100.0)
        g.agregar_arista(Edge(f"N{p}", f"N{i}", costo_instalacion=c, costo_operativo=c * 0.1,
                              capacidad=c, monto=c, n_transferencias=max(1, int(c / 10))))
    aristas_extra = n // 2
    for _ in range(aristas_extra):
        u, v = RNG.randint(0, n - 1), RNG.randint(0, n - 1)
        if u != v:
            c = RNG.uniform(1.0, 100.0)
            g.agregar_arista(Edge(f"N{u}", f"N{v}", costo_instalacion=c, costo_operativo=c * 0.1,
                                  capacidad=c, monto=c, n_transferencias=max(1, int(c / 10))))
    return g


def _grafo_flujo_capas(n_intermedios: int) -> tuple:
    """Genera red de flujo con super-fuente S y super-sumidero T."""
    g = Graph(dirigido=True, ponderado=True)
    g.agregar_nodo(Node("S", "boveda_central"))
    g.agregar_nodo(Node("T", "entidad"))
    for i in range(n_intermedios):
        g.agregar_nodo(Node(f"V{i}", "agencia"))
    primeros = max(1, n_intermedios // 5)
    for i in range(primeros):
        c = RNG.uniform(50.0, 200.0)
        g.agregar_arista(Edge("S", f"V{i}", capacidad=c))
    ultimos = max(1, n_intermedios // 5)
    for i in range(n_intermedios - ultimos, n_intermedios):
        c = RNG.uniform(50.0, 200.0)
        g.agregar_arista(Edge(f"V{i}", "T", capacidad=c))
    for i in range(n_intermedios - 1):
        dest = min(n_intermedios - 1, i + RNG.randint(1, 3))
        c = RNG.uniform(20.0, 150.0)
        g.agregar_arista(Edge(f"V{i}", f"V{dest}", capacidad=c))
    return g


def _medir(fn, *args, reps=3):
    tiempos, mems = [], []
    for _ in range(reps):
        tracemalloc.start()
        t0 = time.perf_counter()
        fn(*args)
        t1 = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        tiempos.append(t1 - t0)
        mems.append(peak / 1024.0)
    return sum(tiempos) / len(tiempos), max(mems)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Curvas de complejidad teórica
# ─────────────────────────────────────────────────────────────────────────────

def grafica_complejidad_teorica():
    n = np.logspace(1, 4, 400)   # Nodos: 10 a 10 000
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Complejidad Temporal Teórica de los Algoritmos – OptiFin", fontsize=14, fontweight="bold")

    # ── Panel 1: Algoritmos de Comunidades ──
    ax = axes[0]
    ax.set_title("Módulo 2: Detección de Comunidades", fontweight="bold")
    E = n * np.log(n)   # E ~ O(N log N) para grafos esparciales
    ax.plot(n, E * np.log(n),  label="Louvain  O(E log V)", color=COLORES["Louvain"],       lw=2.5)
    ax.plot(n, E,              label="Umbral BFS  O(V+E)",  color=COLORES["Umbral"],         lw=2.5, ls="--")
    ax.plot(n, 15 * E,         label="LPA  O(k·E), k≤15",  color=COLORES["LPA"],            lw=2.5, ls="-.")
    ax.plot(n, n**2 * E,       label="Girvan-Newman  O(VE²)", color="#B71C1C",               lw=1.5, ls=":", alpha=0.7)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Número de nodos V"); ax.set_ylabel("Operaciones (escala relativa)")
    ax.legend(fontsize=9); ax.grid(True, which="both", alpha=0.3)

    # ── Panel 2: MST ──
    ax = axes[1]
    ax.set_title("Módulo 3: Árbol de Expansión Mínima", fontweight="bold")
    E_sparse = n * 2       # E ~ 2V (disperso)
    E_dense  = n * n       # E ~ V² (denso)
    ax.plot(n, E_sparse * np.log(E_sparse), label="Kruskal  O(E log E) – esparso", color=COLORES["Kruskal"], lw=2.5)
    ax.plot(n, E_sparse * np.log(n),        label="Prim     O(E log V) – esparso", color=COLORES["Prim"],    lw=2.5, ls="--")
    ax.plot(n, E_dense * np.log(E_dense),   label="Kruskal  O(E log E) – denso",   color=COLORES["Kruskal"], lw=1.5, ls=":", alpha=0.7)
    ax.plot(n, E_dense * np.log(n),         label="Prim     O(E log V) – denso",   color=COLORES["Prim"],    lw=1.5, ls="-.", alpha=0.7)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Número de nodos V"); ax.set_ylabel("Operaciones (escala relativa)")
    ax.legend(fontsize=9); ax.grid(True, which="both", alpha=0.3)

    # ── Panel 3: Flujo Máximo ──
    ax = axes[2]
    ax.set_title("Módulo 4: Flujo Máximo", fontweight="bold")
    E2 = n * 2
    f_val = n * 10          # Flujo f ~ O(10V) para grafos de distribución
    ax.plot(n, n**2 * E2,            label="Dinic  O(V²E)",    color=COLORES["Dinic"],          lw=2.5)
    ax.plot(n, n * E2**2,            label="Edmonds-Karp  O(VE²)", color=COLORES["Edmonds-Karp"], lw=2.5, ls="--")
    ax.plot(n, E2 * f_val,           label="Ford-Fulkerson  O(E·f)", color=COLORES["Ford-Fulkerson"], lw=2.5, ls="-.")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Número de nodos V"); ax.set_ylabel("Operaciones (escala relativa)")
    ax.legend(fontsize=9); ax.grid(True, which="both", alpha=0.3)

    plt.tight_layout()
    ruta = os.path.join(REPORTS_DIR, "complejidad_teorica.png")
    plt.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")
    return ruta


# ─────────────────────────────────────────────────────────────────────────────
# 2. Benchmark empírico MST – Tiempo y pendiente log-log
# ─────────────────────────────────────────────────────────────────────────────

def grafica_benchmark_mst():
    tamanos = [30, 60, 100, 200, 350, 500, 800, 1200]
    t_k, t_p, m_k, m_p, aristas_n = [], [], [], [], []

    for n in tamanos:
        g = _grafo_esparso(n, dirigido=False)
        aristas_n.append(g.num_aristas)
        peso_fn = lambda e: e.costo_instalacion

        tk, mk = _medir(lambda: kruskal_mst(g, peso_fn=peso_fn))
        tp, mp = _medir(lambda: prim_mst(g, peso_fn=peso_fn))
        t_k.append(tk * 1000); t_p.append(tp * 1000)
        m_k.append(mk); m_p.append(mp)

    pend_k = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_k])
    pend_p = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_p])

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Benchmark Empírico – Árbol de Expansión Mínima (MST)", fontsize=14, fontweight="bold")

    # Tiempo vs Nodos
    ax = axes[0]
    ax.plot(tamanos, t_k, "o-", color=COLORES["Kruskal"], lw=2, ms=6, label=f"Kruskal (α={pend_k:.2f})")
    ax.plot(tamanos, t_p, "s--", color=COLORES["Prim"],    lw=2, ms=6, label=f"Prim    (α={pend_p:.2f})")
    ax.set_xlabel("Nodos (V)"); ax.set_ylabel("Tiempo (ms)")
    ax.set_title("Tiempo vs. Nodos"); ax.legend(); ax.grid(alpha=0.3)

    # Log-Log
    ax = axes[1]
    ax.loglog(tamanos, t_k, "o-", color=COLORES["Kruskal"], lw=2, ms=6, label=f"Kruskal α≈{pend_k:.2f}")
    ax.loglog(tamanos, t_p, "s--", color=COLORES["Prim"],    lw=2, ms=6, label=f"Prim    α≈{pend_p:.2f}")
    # Líneas de referencia teóricas
    xs = np.array(tamanos, dtype=float)
    ref_base = t_k[0] / (tamanos[0] * math.log(tamanos[0]) + 1e-9)
    ax.loglog(xs, ref_base * xs * np.log(xs), ":", color="grey", alpha=0.6, label="O(N log N) ref.")
    ax.set_xlabel("Nodos (V)"); ax.set_ylabel("Tiempo (ms) – escala log")
    ax.set_title("Escala Log-Log"); ax.legend(); ax.grid(True, which="both", alpha=0.3)

    # Memoria
    ax = axes[2]
    ax.plot(tamanos, m_k, "o-",  color=COLORES["Kruskal"], lw=2, ms=6, label="Kruskal")
    ax.plot(tamanos, m_p, "s--", color=COLORES["Prim"],    lw=2, ms=6, label="Prim")
    ax.set_xlabel("Nodos (V)"); ax.set_ylabel("Memoria pico (KB)")
    ax.set_title("Uso de Memoria Pico"); ax.legend(); ax.grid(alpha=0.3)

    plt.tight_layout()
    ruta = os.path.join(REPORTS_DIR, "benchmark_mst.png")
    plt.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")
    return ruta


# ─────────────────────────────────────────────────────────────────────────────
# 3. Benchmark empírico Flujo Máximo
# ─────────────────────────────────────────────────────────────────────────────

def grafica_benchmark_flujo():
    tamanos = [20, 40, 80, 150, 250, 350]
    t_d, t_ek, t_ff = [], [], []
    m_d, m_ek, m_ff = [], [], []
    aristas_n = []

    for n in tamanos:
        g = _grafo_flujo_capas(n)
        aristas_n.append(g.num_aristas)

        td, md   = _medir(lambda: dinic_flujo_maximo(construir_red_residual_desde_grafo(g, "S", "T"), "S", "T"))
        tek, mek = _medir(lambda: edmonds_karp_flujo_maximo(construir_red_residual_desde_grafo(g, "S", "T"), "S", "T"))
        tff, mff = _medir(lambda: ford_fulkerson_dfs(construir_red_residual_desde_grafo(g, "S", "T"), "S", "T"))

        t_d.append(td * 1000);  t_ek.append(tek * 1000); t_ff.append(tff * 1000)
        m_d.append(md);          m_ek.append(mek);          m_ff.append(mff)

    pend_d  = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_d])
    pend_ek = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_ek])
    pend_ff = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_ff])

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Benchmark Empírico – Algoritmos de Flujo Máximo", fontsize=14, fontweight="bold")

    # Tiempo vs Nodos
    ax = axes[0]
    ax.plot(tamanos, t_d,  "o-",  color=COLORES["Dinic"],          lw=2, ms=6, label=f"Dinic (α={pend_d:.2f})")
    ax.plot(tamanos, t_ek, "s--", color=COLORES["Edmonds-Karp"],   lw=2, ms=6, label=f"Edmonds-Karp (α={pend_ek:.2f})")
    ax.plot(tamanos, t_ff, "^-.", color=COLORES["Ford-Fulkerson"], lw=2, ms=6, label=f"Ford-Fulkerson (α={pend_ff:.2f})")
    ax.set_xlabel("Nodos intermedios"); ax.set_ylabel("Tiempo (ms)")
    ax.set_title("Tiempo vs. Tamaño de Red"); ax.legend(fontsize=9); ax.grid(alpha=0.3)

    # Log-Log
    ax = axes[1]
    ax.loglog(tamanos, t_d,  "o-",  color=COLORES["Dinic"],          lw=2, ms=6, label=f"Dinic α≈{pend_d:.2f}")
    ax.loglog(tamanos, t_ek, "s--", color=COLORES["Edmonds-Karp"],   lw=2, ms=6, label=f"Edmonds-Karp α≈{pend_ek:.2f}")
    ax.loglog(tamanos, t_ff, "^-.", color=COLORES["Ford-Fulkerson"], lw=2, ms=6, label=f"Ford-Fulkerson α≈{pend_ff:.2f}")
    xs = np.array(tamanos, dtype=float)
    ax.loglog(xs, xs**2 / xs[0]**2 * t_d[0],    ":", color="grey", alpha=0.5, label="O(N²) ref.")
    ax.loglog(xs, xs**1.5 / xs[0]**1.5 * t_d[0], "-", color="silver", alpha=0.5, lw=1, label="O(N^1.5) ref.")
    ax.set_xlabel("Nodos intermedios"); ax.set_ylabel("Tiempo (ms) – escala log")
    ax.set_title("Escala Log-Log"); ax.legend(fontsize=8); ax.grid(True, which="both", alpha=0.3)

    # Memoria
    ax = axes[2]
    ax.plot(tamanos, m_d,  "o-",  color=COLORES["Dinic"],          lw=2, ms=6, label="Dinic")
    ax.plot(tamanos, m_ek, "s--", color=COLORES["Edmonds-Karp"],   lw=2, ms=6, label="Edmonds-Karp")
    ax.plot(tamanos, m_ff, "^-.", color=COLORES["Ford-Fulkerson"], lw=2, ms=6, label="Ford-Fulkerson")
    ax.set_xlabel("Nodos intermedios"); ax.set_ylabel("Memoria pico (KB)")
    ax.set_title("Uso de Memoria Pico"); ax.legend(fontsize=9); ax.grid(alpha=0.3)

    plt.tight_layout()
    ruta = os.path.join(REPORTS_DIR, "benchmark_flujo.png")
    plt.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")
    return ruta


# ─────────────────────────────────────────────────────────────────────────────
# 4. Comparación de modularidad y tiempo – Algoritmos de Comunidades
# ─────────────────────────────────────────────────────────────────────────────

def grafica_benchmark_comunidades():
    tamanos = [20, 50, 100, 200, 400, 600]
    t_louv, t_lpa, t_umbral = [], [], []
    q_louv, q_lpa, q_umbral = [], [], []
    m_louv, m_lpa, m_umbral = [], [], []

    peso_fn = lambda e: float(e.n_transferencias) * math.log1p(max(0.0, float(e.monto)))

    for n in tamanos:
        g = _grafo_esparso(n, dirigido=False)
        louvain = AlgoritmoLouvain()
        umbral_val = 2.0

        # Louvain
        t0 = time.perf_counter(); tracemalloc.start()
        part_l, q_l, _ = louvain.ejecutar_una_corrida(g, peso_fn=peso_fn, seed=42)
        t1 = time.perf_counter(); _, pk_l = tracemalloc.get_traced_memory(); tracemalloc.stop()
        t_louv.append((t1 - t0) * 1000); m_louv.append(pk_l / 1024)
        q_louv.append(calcular_modularidad(g, part_l, peso_fn=peso_fn))

        # LPA
        t0 = time.perf_counter(); tracemalloc.start()
        part_lpa = propagacion_etiquetas(g, peso_fn=peso_fn, seed=42)
        t1 = time.perf_counter(); _, pk_lpa = tracemalloc.get_traced_memory(); tracemalloc.stop()
        t_lpa.append((t1 - t0) * 1000); m_lpa.append(pk_lpa / 1024)
        q_lpa.append(calcular_modularidad(g, part_lpa, peso_fn=peso_fn))

        # Umbral BFS
        t0 = time.perf_counter(); tracemalloc.start()
        part_u = componentes_por_umbral_bfs(g, umbral_val, peso_fn=peso_fn)
        t1 = time.perf_counter(); _, pk_u = tracemalloc.get_traced_memory(); tracemalloc.stop()
        t_umbral.append((t1 - t0) * 1000); m_umbral.append(pk_u / 1024)
        q_umbral.append(calcular_modularidad(g, part_u, peso_fn=peso_fn))

    pend_l = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_louv])
    pend_lpa = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_lpa])
    pend_u = estimar_pendiente_log_log(tamanos, [x / 1000 for x in t_umbral])

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Benchmark Empírico – Algoritmos de Detección de Comunidades", fontsize=14, fontweight="bold")

    # Tiempo
    ax = axes[0]
    ax.plot(tamanos, t_louv,  "o-",  color=COLORES["Louvain"], lw=2, ms=6, label=f"Louvain  (α={pend_l:.2f})")
    ax.plot(tamanos, t_lpa,   "s--", color=COLORES["LPA"],     lw=2, ms=6, label=f"LPA      (α={pend_lpa:.2f})")
    ax.plot(tamanos, t_umbral,"^-.", color=COLORES["Umbral"],  lw=2, ms=6, label=f"Umbral   (α={pend_u:.2f})")
    ax.set_xlabel("Nodos (V)"); ax.set_ylabel("Tiempo (ms)")
    ax.set_title("Tiempo de Ejecución vs. Tamaño"); ax.legend(); ax.grid(alpha=0.3)

    # Modularidad
    ax = axes[1]
    ax.plot(tamanos, q_louv,  "o-",  color=COLORES["Louvain"], lw=2, ms=6, label="Louvain")
    ax.plot(tamanos, q_lpa,   "s--", color=COLORES["LPA"],     lw=2, ms=6, label="LPA")
    ax.plot(tamanos, q_umbral,"^-.", color=COLORES["Umbral"],  lw=2, ms=6, label="Umbral")
    ax.axhline(0.3, color="grey", ls=":", lw=1.2, label="Q=0.3 (umbral bueno)")
    ax.set_xlabel("Nodos (V)"); ax.set_ylabel("Modularidad Q")
    ax.set_title("Calidad de Partición (Modularidad Q)"); ax.legend(); ax.grid(alpha=0.3)
    ax.set_ylim(-0.05, 1.0)

    # Memoria
    ax = axes[2]
    ax.plot(tamanos, m_louv,  "o-",  color=COLORES["Louvain"], lw=2, ms=6, label="Louvain")
    ax.plot(tamanos, m_lpa,   "s--", color=COLORES["LPA"],     lw=2, ms=6, label="LPA")
    ax.plot(tamanos, m_umbral,"^-.", color=COLORES["Umbral"],  lw=2, ms=6, label="Umbral")
    ax.set_xlabel("Nodos (V)"); ax.set_ylabel("Memoria pico (KB)")
    ax.set_title("Uso de Memoria Pico"); ax.legend(); ax.grid(alpha=0.3)

    plt.tight_layout()
    ruta = os.path.join(REPORTS_DIR, "benchmark_comunidades.png")
    plt.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")
    return ruta


# ─────────────────────────────────────────────────────────────────────────────
# 5. Panel resumen: todas las complejidades teóricas juntas (tabla visual)
# ─────────────────────────────────────────────────────────────────────────────

def grafica_resumen_complejidades():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.axis("off")

    datos = [
        ["Módulo", "Algoritmo", "Complejidad Tiempo", "Complejidad Espacio", "Determinista", "Calidad/Uso"],
        ["M1 – Grafo", "Lista de Adyacencia",   "O(1) add / O(deg) iter",  "O(V + E)",   "Sí", "Estructura base"],
        ["M1 – Recorrido", "BFS / DFS",          "O(V + E)",               "O(V)",        "Sí", "Distancias mínimas"],
        ["M1 – Recorrido", "Union-Find",          "O(α(N)) por op.",        "O(N)",        "Sí", "Componentes, MST"],
        ["M1 – Recorrido", "Low-Link (Tarjan)",   "O(V + E)",               "O(V)",        "Sí", "Puentes y articulaciones"],
        ["M2 – Fraude", "Umbral BFS",             "O(V + E)",               "O(V + E)",   "Sí", "Rápido, umbral manual"],
        ["M2 – Fraude", "LPA ponderada",          "O(k · E), k ≤ 15",       "O(V + E)",   "No", "Rápido, sin umbral"],
        ["M2 – Fraude", "Louvain",                "O(E log V) empírico",    "O(V + E)",   "No", "Alta modularidad"],
        ["M3 – MST", "Kruskal + Union-Find",      "O(E log E)",             "O(V + E)",   "Sí", "Óptimo en esparciales"],
        ["M3 – MST", "Prim + Min-Heap",           "O(E log V)",             "O(V + E)",   "Sí", "Óptimo en densos"],
        ["M4 – Flujo", "Ford-Fulkerson DFS",      "O(E · f)",               "O(V + E)",   "No", "Simple, lento con f grande"],
        ["M4 – Flujo", "Edmonds-Karp",            "O(V · E²)",              "O(V + E)",   "Sí", "Polinomial garantizado"],
        ["M4 – Flujo", "Dinic",                   "O(V² · E)",              "O(V + E)",   "Sí", "O(E√V) en capas – óptimo"],
    ]

    n_col = len(datos[0])
    colores_fila = []
    for i in range(len(datos)):
        if i == 0:
            colores_fila.append(["#1565C0"] * n_col)
        elif "M2" in datos[i][0]:
            colores_fila.append(["#E3F2FD"] * n_col)
        elif "M3" in datos[i][0]:
            colores_fila.append(["#E8F5E9"] * n_col)
        elif "M4" in datos[i][0]:
            colores_fila.append(["#FFF3E0"] * n_col)
        else:
            colores_fila.append(["#F5F5F5"] * n_col)

    tabla = ax.table(
        cellText=datos[1:],
        colLabels=datos[0],
        cellLoc="center",
        loc="center",
        cellColours=colores_fila[1:],
        colColours=colores_fila[0],
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(9.5)
    tabla.scale(1.0, 1.9)

    # Cabecera en blanco sobre azul oscuro
    for j in range(n_col):
        tabla[0, j].set_text_props(color="white", fontweight="bold")

    ax.set_title("Resumen de Complejidades Algorítmicas – OptiFin", fontsize=14, fontweight="bold", pad=10)

    plt.tight_layout()
    ruta = os.path.join(REPORTS_DIR, "resumen_complejidades.png")
    plt.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")
    return ruta


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("[OptiFin] Generando gráficas de complejidad algorítmica...\n")
    rutas = []
    rutas.append(grafica_complejidad_teorica())
    rutas.append(grafica_benchmark_mst())
    rutas.append(grafica_benchmark_flujo())
    rutas.append(grafica_benchmark_comunidades())
    rutas.append(grafica_resumen_complejidades())

    print(f"\n[OptiFin] {len(rutas)} gráficas generadas en '{REPORTS_DIR}/':")
    for r in rutas:
        print(f"  → {os.path.basename(r)}")


if __name__ == "__main__":
    main()
