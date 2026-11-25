# OptiFin – Informe Técnico Final

## 1. Descripción del Sistema

**OptiFin** es un sistema en Python 3 para el modelado de redes financieras como grafos y la resolución de tres escenarios críticos del sector bancario utilizando algoritmos de grafos implementados desde cero.

### Escenarios Implementados

| Escenario | Caso | Algoritmo Principal | Alternativas |
|---|---|---|---|
| Fraude y Lavado | Detección de comunidades (redes de mulas) | Louvain | Umbral BFS/Union-Find, LPA |
| Enrutamiento | Red troncal de menor costo | Kruskal + Union-Find | Prim + Min-Heap |
| Liquidez | Cuellos de botella en distribución de efectivo | Dinic + Corte Mínimo | Edmonds-Karp, Ford-Fulkerson |

---

## 2. Arquitectura del Sistema

```
proyecto_optifin/
├── main.py                       # CLI interactiva y no interactiva
├── src/
│   ├── graph.py                  # Módulo 1A: Estructura Graph, Node, Edge
│   ├── gestion_red.py            # Módulo 1B: Carga, validación, persistencia
│   ├── visualizacion.py          # Visualización con matplotlib/networkx
│   ├── analisis_transacciones.py # Módulo 2: Orquestador comunidades y fraude
│   ├── enrutamiento_financiero.py# Módulo 3: Orquestador MST y rutas
│   ├── distribucion_liquidez.py  # Módulo 4: Orquestador flujo y corte
│   ├── evaluacion_resultados.py  # Módulo 5: Benchmarks y casos difíciles
│   ├── utils.py                  # Utilidades transversales
│   └── algoritmos/               # Algoritmos puros (sin acoplamiento de negocio)
│       ├── union_find.py         # Union-Find con compresión de caminos
│       ├── recorridos.py         # BFS, DFS, puentes, articulaciones
│       ├── comunidades.py        # Louvain, LPA, Umbral, Modularidad
│       ├── arbol_expansion.py    # Kruskal, Prim
│       └── flujo.py              # Dinic, Edmonds-Karp, Ford-Fulkerson, Corte Mínimo
├── tests/                        # 30 pruebas con oráculos NetworkX
├── data/                         # Datos sintéticos generados reproduciblemente
├── reports/                      # Reportes Markdown generados en ejecución
├── scripts/generar_datos.py      # Generador de datos con semilla configurable
└── docs/                         # Documentación técnica
```

### Principios Arquitectónicos
- **Separación de responsabilidades:** los algoritmos en `src/algoritmos/` son independientes de la lógica de negocio financiera; los módulos de orquestación en `src/` coordinan preprocesamiento, algoritmos y reportes.
- **Sin acoplamiento circular:** `graph.py` ← `algoritmos/` ← `gestion_red.py`, `analisis_transacciones.py`, etc.
- **NetworkX solo en tests y visualización:** garantía de implementación propia.

---

## 3. Resultados de Ejecución (Demo con seed=42)

### Módulo 2 – Detección de Comunidades
- Red: 31 nodos, 61 aristas transaccionales
- Modularidad Louvain: **Q = 0.5919**
- Estabilidad multisemilla: **100%**
- Comunidades detectadas: 11
- Ahorro de tiempo frente a Girvan-Newman: >99.9% (evita O(VE²) iteraciones)

### Módulo 3 – Red Troncal
- Red: 18 nodos (sedes, agencias, ATM), 32 enlaces candidatos
- Costo MST Kruskal: **\$74,785.70**
- Costo MST Prim: **\$74,785.70** (coincidencia exacta verificada)
- Ahorro vs. red completa: **\$108,437.71 (59.2%)**
- Tiempo Kruskal: 0.14 ms | Tiempo Prim: 0.15 ms

### Módulo 4 – Distribución de Liquidez
- Red: 14 nodos (2 bóvedas centrales, 3 regionales, 6 agencias, 3 ATMs)
- Flujo máximo (Dinic): **\$1,825,000.00**
- Flujo máximo Edmonds-Karp: **\$1,825,000.00** ✓ (coincidencia)
- Déficit de liquidez: **\$120,000.00** (en AG-LIMA-02 limitada a 300k por cuello)
- Teorema Max-Flow / Min-Cut: **VERIFICADO**
- Inversión prioritaria: ampliar REG-NORTE → AG-LIMA-02 → ganancia marginal +\$50,000/δ

---

## 4. Suite de Pruebas

| Archivo | Pruebas | Cobertura |
|---|---|---|
| test_graph.py | 5 | Graph, Node, Edge |
| test_gestion_red.py | 2 | Carga CSV/JSON, validación |
| test_recorridos_uf.py | 3 | BFS, DFS, Union-Find, puentes |
| test_comunidades.py | 5 | Louvain, LPA, Umbral, oráculo NX |
| test_enrutamiento.py | 5 | Kruskal, Prim, restricciones, oráculo NX |
| test_liquidez.py | 5 | Dinic, EK, FF, corte, oráculo NX, casos borde |
| test_evaluacion.py | 5 | Benchmarks, pendiente log-log, casos difíciles |
| **Total** | **30** | **30/30 PASA** |

Los tests de oráculo comparan los resultados implementados desde cero contra NetworkX (`minimum_spanning_tree`, `maximum_flow`, `minimum_cut`, `modularity`) verificando coincidencia dentro de tolerancia relativa de 10⁻⁵.

---

## 5. Validación del Caso Obligatorio del Tema 5

Red de 8 cuentas con pesos = número de transferencias:

| Verificación | Resultado | Estado |
|---|---|---|
| Umbral 1 → 1 componente | ✓ | PASA |
| Umbral 2 → {A..G} y {H} | ✓ | PASA |
| Umbrales 3-7 → {ABCD}, {EFG}, {H} | ✓ | PASA |
| Umbral 8+ → se parte grupo real | ✓ | PASA |
| Louvain: {ABCD} y {EFG}, H frontera, Q > 0.3 | Q = 0.3734 | PASA |
| LPA: mismos 2 grupos | ✓ | PASA |
| Modularidad propia = NetworkX | Δ < 10⁻⁴ | PASA |

---

## 6. Casos Difíciles Adversarios (Módulo 5)

| Caso | Descripción | Louvain | LPA | Umbral Alto |
|---|---|---|---|---|
| A: Concentrador | Nómina conecta artificialmente 2 clusters independientes | ❌ sin exclusión / ✓ con exclusión | Igual | Mezcla grupos |
| B: Mulas débiles | 5 cuentas con microtransacciones (monto < 9,800) | ✓ Detecta cluster | ✓ Detecta cluster | ❌ Pierde mulas |
| C: Puente fuerte | 2 clusters densos unidos por 1 arista de peso alto | ✓ Separa correctamente | Variable | Depende del umbral |

**Conclusión validada:** Louvain con exclusión de concentradores supera a las líneas base en los 3 casos difíciles. El umbral fijo es el más vulnerable ante variaciones de escala de peso.

---

## 7. Instrucciones de Uso

### Instalación
```bash
pip install -r requirements.txt
```

### Generar Datos
```bash
python scripts/generar_datos.py --seed 42
```

### Ejecutar
```bash
# Demo completa (no interactivo)
python main.py --demo

# Módulo específico
python main.py --modulo 2
python main.py --modulo 3 --datos data/red_troncal.json
python main.py --modulo 4 --datos data/distribucion_liquidez.json

# Benchmarks
python main.py --benchmark

# Menú interactivo
python main.py
```

### Pruebas
```bash
pytest -v                                              # Todos los tests
pytest tests/test_comunidades.py -v                    # Solo Módulo 2
pytest --cov=src --cov-report=term-missing             # Con cobertura
```
