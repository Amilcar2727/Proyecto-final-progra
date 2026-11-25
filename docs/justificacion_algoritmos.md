# Justificación de Algoritmos – OptiFin

## 1. Estructura de Datos Base: Grafo con Lista de Adyacencia

**Decisión:** `dict[str, dict[str, list[Edge]]]`

| Criterio | Lista de Adyacencia | Matriz de Adyacencia |
|---|---|---|
| Espacio | O(V + E) | O(V²) |
| Iterar vecinos | O(deg(v)) | O(V) |
| Verificar arista (u,v) | O(deg(u)) | O(1) |
| Agregar nodo | O(1) | O(V²) rehash |
| Mejor cuando | Redes esparsas |V|E| << V²| Redes densas, consultas directas |

Las redes financieras reales tienen densidades típicas de 10⁻³ a 10⁻⁵ (una cuenta interactúa con un pequeño subconjunto del universo de cuentas). Para 10,000 cuentas, una matriz requeriría 100M de celdas vs. unas pocas decenas de miles de entradas en lista de adyacencia.

---

## 2. Módulo 2: Detección de Comunidades para Prevención de Fraude

### 2.1 Algoritmo Principal: Louvain

**Por qué Louvain y no otros:**

| Algoritmo | Complejidad | Determinismo | Escala | Modularidad |
|---|---|---|---|---|
| **Louvain** | O(E log V) empírico | No (semilla) | Millones nodos | Óptima heurística |
| Girvan-Newman | O(V E²) | Sí | <1000 nodos | Buena |
| Espectral | O(V³) | Sí | <10000 nodos | Buena |
| Umbral BFS | O(V + E) | Sí | Ilimitada | Fija por umbral |
| LPA | O(k E) | No (semilla) | Millones nodos | Variable |

**Pertinencia:** El problema de fraude por redes de cuentas mula requiere:
1. **Escala:** redes bancarias reales tienen millones de cuentas → Girvan-Newman es inviable.
2. **Estructura de comunidades no trivial:** los clusters de fraude son grupos cohesivos de densidad interna alta pero con pocos vínculos externos → Louvain optimiza exactamente la función de modularidad que captura esto.
3. **Sin parámetros de corte manual:** a diferencia del umbral, Louvain descubre automáticamente el número de comunidades.

**Límites conocidos y documentados:**
- El problema de resolución de Louvain: comunidades con menos de √(2m) aristas son sistemáticamente ignoradas.
- No tiene garantía teórica de convergencia a un óptimo global.
- Dependencia de semilla → se mitiga con ejecución multi-semilla.

**Modularidad con resolución γ:**
$$Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \gamma \cdot \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$

**ΔQ incremental** (Fase 1, O(1) por vecino mediante Σin y Σtot):
$$\Delta Q = \frac{k_{i,in}}{2m} - \gamma \frac{k_i \cdot \Sigma_{tot}}{(2m)^2}$$

### 2.2 Línea base 1: Componentes por Umbral con BFS y Union-Find

- **BFS:** O(V + E). Determinista, intuitivo para analistas sin conocimiento técnico.
- **Union-Find:** O(E α(V)) amortizado. Permite actualizaciones incrementales: cuando llega una nueva transacción solo se requiere una operación union() en O(α(V)), sin recalcular toda la partición.
- **Pertinencia como línea base:** permite calibrar el umbral de peso mínimo para que dos cuentas se consideren "relacionadas", y producir un análisis paramétrico de sensibilidad (barrido de umbrales).

### 2.3 Línea base 2: Propagación de Etiquetas (LPA)

- **Complejidad:** O(k · E), con k ≤ 15 rondas empíricas típicas.
- **Ventaja sobre umbral:** no requiere definir un umbral; propaga naturalmente la influencia de vecindades.
- **Desventaja vs. Louvain:** propenso a soluciones triviales (todo en una comunidad) en grafos muy densos; sin jerarquía de comunidades; sin medida objetiva de calidad análoga a la modularidad.

---

## 3. Módulo 3: Red Troncal de Menor Costo (MST)

### 3.1 Algoritmo Principal: Kruskal + Union-Find

**Complejidad:** O(E log E) por el ordenamiento de aristas.
**Espacio:** O(V + E).

**Por qué Kruskal:**
1. El problema de diseño de red troncal financiera genera un grafo **esparso**: pocas sedes con múltiples enlaces candidatos pero no todos pares conectados (E << V²). Para grafos esparciales Kruskal es más eficiente que Prim porque su cuello de botella es el ordenamiento O(E log E) y no depende de V.
2. Union-Find permite agregar la restricción de aristas obligatorias: se fuerzan primero en el bosque y el resto del algoritmo respeta la invariante de acicidad.
3. Detecta naturalmente bosques: si la red candidata es desconectada, produce el Bosque de Expansión Mínima óptimo e identifica componentes aisladas.

### 3.2 Comparación: Prim + Min-Heap Binario

**Complejidad:** O(E log V) con heap binario; O(E + V log V) con Fibonacci heap.
**Pertinencia en contexto financiero:**
- Prim es más eficiente en grafos **densos** (cuando E ≈ V²) porque no ordena todas las aristas.
- En la demo con 18 nodos y 32 aristas (E/V ≈ 1.8), ambos producen idéntico peso y tiempos comparables.
- El benchmark a escala mayor muestra que Kruskal permanece competitivo hasta densidades medias.

### 3.3 Fragilidad: DFS Low-Link (Tarjan)

**Complejidad:** O(V + E).

Un MST es inherentemente frágil (todo árbol tiene V-1 puentes). El análisis de Tarjan sobre el árbol resultante identifica:
- **Puentes:** enlaces cuya falla parte la red. En un árbol, cada arista es puente.
- **Puntos de articulación:** nodos cuya falla desconecta el árbol. Son todos los nodos internos con grado > 1.
- **Sugerencias de redundancia:** se seleccionan los enlaces adicionales de menor costo del grafo original que cierren ciclos en torno a los puntos críticos.

---

## 4. Módulo 4: Distribución de Liquidez – Flujo y Corte Mínimo

### 4.1 Algoritmo Principal: Dinic

**Complejidad teórica:** O(V² E).
**Complejidad práctica:** mucho mejor en redes unitarias y grafos en capas como las de distribución bancaria.

**Por qué Dinic:**
1. Las redes de distribución de efectivo son grafos estratificados (bóvedas → regionales → agencias), el caso donde Dinic es asintóticamente O(E √V) — óptimo entre los algoritmos prácticos.
2. Los **punteros de avance** (work pointer) garantizan que cada arista del grafo de nivel sea visitada a lo sumo una vez por fase, evitando el retroceso redundante de Edmonds-Karp.
3. El BFS de construcción del grafo de nivel produce automáticamente el **corte mínimo** tras el último BFS sin camino aumentante.

**Teorema Max-Flow / Min-Cut verificado empíricamente:**
Tras cada ejecución, el sistema verifica que `flujo_máximo = capacidad_del_corte_mínimo` con tolerancia 10⁻⁴.

### 4.2 Comparación: Edmonds-Karp

**Complejidad:** O(V E²).
**Pertinencia:** Es la variante de Ford-Fulkerson con la complejidad polinomial más ajustada al garantizar que usa siempre el camino más corto (BFS). En redes pequeñas, es perfectamente viable y más simple de implementar. En el benchmark, es comparable a Dinic hasta unas 300 aristas.

### 4.3 Comparación: Ford-Fulkerson (DFS)

**Complejidad:** O(E · f), donde f es el valor del flujo máximo.
**Limitación crítica:** En redes con capacidades no enteras o muy grandes (como los montos de efectivo en millones de USD), puede ejecutar O(10⁶) iteraciones. Solo se benchmarka hasta redes de 300 aristas para evitar tiempos exponenciales.

### 4.4 Distinción: Saturadas vs. Cuellos de Botella Reales

Esta distinción es fundamental para la correcta priorización de inversiones:

- **Arista saturada:** flujo == capacidad. Puede existir por múltiples razones que no implican ser cuello de botella.
- **Cuello de botella real (corte mínimo):** arista que pertenece al corte mínimo S→T en el grafo residual. Su ampliación **siempre** produce un incremento en el flujo global (hasta el próximo corte mínimo alternativo).

**Ejemplo:** Si la ruta A→B está saturada pero existe un camino alternativo A→C→B con capacidad residual, entonces A→B no es cuello de botella: la red puede seguir fluyendo sin ampliar A→B.

### 4.5 Análisis de Sensibilidad Marginal

Para cada arista del corte mínimo, se aumenta su capacidad en δ = 50,000 USD y se recalcula el flujo con Dinic. La ganancia marginal = nuevo_flujo − flujo_base cuantifica exactamente cuánto efectivo adicional llegaría a las agencias por cada USD invertido en ampliar esa ruta de transporte.

---

## 5. Resumen de Selecciones Algorítmicas

| Módulo | Problema | Algoritmo | Justificación Principal |
|---|---|---|---|
| 2 | Detección de fraude | **Louvain** | Escala O(E log V), descubrimiento automático de clusters, maximización de modularidad |
| 2 | Línea base | Umbral BFS + Union-Find | Determinismo, O(V+E), soporte incremental para streams de transacciones |
| 2 | Línea base | LPA ponderada | O(kE), rápida, complementa a Louvain en escenarios con muchas componentes pequeñas |
| 3 | MST de red troncal | **Kruskal + Union-Find** | O(E log E), natural en grafos esparciales, soporte nativo de aristas obligatorias/prohibidas |
| 3 | Comparación MST | Prim + Min-Heap | O(E log V), superior en grafos densos y con nodo de inicio conocido |
| 4 | Flujo máximo | **Dinic** | O(V²E), práctico O(E√V) en grafos estratificados como redes de distribución |
| 4 | Comparación flujo | Edmonds-Karp | O(VE²), polinomial garantizado sin patologías de Ford-Fulkerson |
| 4 | Comparación flujo | Ford-Fulkerson DFS | O(Ef), simple, útil para capacidades pequeñas, no recomendado con montos grandes |
