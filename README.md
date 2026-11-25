# OptiFin – Sistema de Análisis y Optimización de Redes Financieras

**Programación III | Teoría de Grafos Aplicada a Finanzas**

---

## Descripción

OptiFin modela redes financieras como grafos e implementa tres escenarios críticos del sector bancario usando **algoritmos implementados desde cero** en Python 3:

| Módulo | Escenario | Algoritmo Principal |
|---|---|---|
| 2 | Detección de comunidades (fraude / lavado) | **Louvain** con multi-semilla |
| 3 | Red troncal de menor costo | **Kruskal + Union-Find** |
| 4 | Distribución de liquidez – cuellos de botella | **Dinic** + Corte Mínimo |

---

## Instalación

```bash
pip install -r requirements.txt
```

**Dependencias:** `matplotlib`, `networkx` (solo visualización y oráculos de test), `pytest`, `pytest-cov`.

La interfaz web local usa `streamlit` y `plotly`. NetworkX se utiliza únicamente para ubicar los nodos en los diagramas; el análisis sigue usando los algoritmos propios del proyecto.

> **Nota:** `networkx` **no** se usa para resolver ningún problema. Solo para verificación cruzada en tests y visualización de layouts.

---

## Uso Rápido

```bash
# Generar datos sintéticos reproducibles
python scripts/generar_datos.py

# Demo completa de los 3 módulos (no interactiva)
python main.py --demo

# Menú interactivo
python main.py

# Interfaz local para explorar los grafos y gráficos
streamlit run app.py

# Módulo específico con datos personalizados
python main.py --modulo 2
python main.py --modulo 3 --datos data/red_troncal.json
python main.py --modulo 4 --datos data/distribucion_liquidez.json

# Benchmarks de rendimiento
python main.py --benchmark

# Ejecutar toda la suite de pruebas
pytest -v
```

---

## Resultados Destacados (seed=42)

| Métrica | Valor |
|---|---|
| Modularidad Louvain (red de fraude) | Q = 0.5919 |
| Estabilidad multi-semilla | 100% |
| Ahorro en red troncal vs. red completa | \$108,437 (59.2%) |
| Flujo máximo distribución | \$1,825,000 |
| Teorema Max-Flow / Min-Cut | ✓ Verificado |
| Pruebas automatizadas | **30/30 PASAN** |

---

## Estructura del Repositorio

```
proyecto_optifin/
├── main.py                        # Punto de entrada
├── requirements.txt
├── data/                          # Datasets sintéticos
│   ├── transacciones.json         # Red de fraude (Módulo 2)
│   ├── red_troncal.json           # Infraestructura (Módulo 3)
│   └── distribucion_liquidez.json # Efectivo (Módulo 4)
├── scripts/generar_datos.py       # Generador reproducible
├── src/
│   ├── graph.py                   # Estructura Graph, Node, Edge
│   ├── gestion_red.py             # Carga CSV/JSON y validación
│   ├── analisis_transacciones.py  # Orquestador Módulo 2
│   ├── enrutamiento_financiero.py # Orquestador Módulo 3
│   ├── distribucion_liquidez.py   # Orquestador Módulo 4
│   ├── evaluacion_resultados.py   # Benchmarks y validación (Módulo 5)
│   └── algoritmos/
│       ├── union_find.py          # Union-Find O(α N)
│       ├── recorridos.py          # BFS, DFS, puentes
│       ├── comunidades.py         # Louvain, LPA, Umbral, Modularidad
│       ├── arbol_expansion.py     # Kruskal, Prim
│       └── flujo.py               # Dinic, Edmonds-Karp, Ford-Fulkerson
├── tests/                         # 30 pruebas con oráculos NetworkX
├── reports/                       # Reportes Markdown generados
└── docs/
    ├── decisiones.md              # Decisiones de diseño justificadas
    ├── justificacion_algoritmos.md# Análisis técnico de algoritmos
    └── informe.md                 # Informe final
```

---

## Garantías de Correctitud

Todos los algoritmos propios son verificados contra oráculos de NetworkX:

- `networkx.minimum_spanning_tree` → Kruskal y Prim (tolerancia relativa 10⁻⁵)
- `networkx.maximum_flow` y `minimum_cut` → Dinic, Edmonds-Karp, Ford-Fulkerson
- `networkx.algorithms.community.modularity` → función `calcular_modularidad`

---

## Gráficas de Complejidad Algorítmica

```bash
python scripts/graficar_complejidad.py
```

Genera en `reports/` las gráficas de complejidad teórica, benchmarks empíricos con pendiente log-log y uso de memoria pico (`complejidad_teorica.png`, `benchmark_mst.png`, `benchmark_flujo.png`, `benchmark_comunidades.png`, `resumen_complejidades.png`).
