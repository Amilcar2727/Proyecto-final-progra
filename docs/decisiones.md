# Registro de Decisiones de Diseño y Arquitectura - OptiFin

## 1. Contexto y Objetivos
Este documento registra formalmente las decisiones técnicas, asunciones operativas y justificaciones de diseño tomadas durante el desarrollo del sistema **OptiFin – Sistema de Análisis y Optimización de Redes Financieras**.

---

## 2. Decisiones de Estructura de Datos y Modelado (Módulo 1)
- **Representación del Grafo (`src/graph.py`):**
  - **Estructura elegida:** Lista de adyacencia implementada mediante diccionarios enlazados: `dict[str, dict[str, list[Edge]]]`.
  - **Justificación:** Las redes financieras reales (cuentas bancarias, rutas de transporte de efectivo, topología de sucursales) son marcadamente dispersas ($|E| \ll |V|^2$). Una representación por lista de adyacencia requiere espacio $O(V + E)$ frente al espacio $O(V^2)$ de una matriz de adyacencia. Además, las operaciones críticas como listar vecinos e iterar sobre aristas salientes toman tiempo proporcional al grado del nodo $O(\text{deg}(v))$ en lugar de $O(V)$. La matriz de adyacencia solo sería preferible en grafos extremadamente densos ($E \approx V^2$) o cuando la operación predominante sea verificar la existencia de una arista entre pares arbitrarios en $O(1)$ sin importar el consumo de memoria.
  - **Soporte multígrafo/aristas múltiples:** Un origen y destino pueden registrar múltiples transferencias en instantes distintos; por ello, la estructura interna soporta lista de aristas por par `(u, v)`.
  - **Función de peso flexible (`peso_fn`):** Permite a los algoritmos abstraer el criterio de optimización (comisión, costo total, latencia, monto, capacidad residual, riesgo).

---

## 3. Decisiones del Módulo 2: Fraude y Lavado de Activos
- **Transformación a Grafo No Dirigido:**
  - En redes de estructuración o cuentas mula (*smurfing* y *layering*), las redes criminales transfieren fondos bidireccionalmente o en bucles triangulares. Para la detección de comunidades de colusión, se proyecta a un grafo no dirigido sumando las transferencias en ambas direcciones ($w(u,v) = w(u \to v) + w(v \to u)$).
- **Métrica de Peso por Defecto:**
  - Por defecto se emplea una métrica combinada $w = n \cdot \ln(1 + \text{monto})$, balanceando la recurrencia transaccional con la magnitud económica, evitando que una única transferencia aislada gigante domine espuriamente la modularidad.
- **Ventana de Tiempo y Concentradores:**
  - Ventana por defecto de 30 días para evaluar actividad operativa reciente.
  - Cuentas con grado en el percentil superior ($\ge 99$) o identificadas como concentradoras legítimas (ej. pago de planillas, servicios públicos) son neutralizadas o excluidas opcionalmente para evitar el efecto de supernodo que aglutina comunidades artificiales.
- **Algoritmo Louvain:**
  - Implementado estrictamente desde cero con optimización modular incremental ($\Delta Q$) en $O(1)$ por vecino en la Fase 1 y contracción de comunidades en supernodos en la Fase 2.
  - Se ejecuta sobre múltiples semillas (`n_corridas`) para seleccionar la de mayor modularidad $Q$ y evaluar estabilidad empírica.

---

## 4. Decisiones del Módulo 3: Enrutamiento Troncal (MST)
- **Algoritmo Principal:** Kruskal con Union-Find (rango y compresión de caminos) con complejidad $O(E \log E)$.
- **Algoritmo de Comparación:** Prim con min-heap binario ($O(E \log V)$).
- **Manejo de Bosques:** Si la red es desconectada, se obtiene un Bosque de Expansión Mínima (MSF), listando componentes aisladas.
- **Análisis de Fragilidad:** Cálculo de puentes y puntos de articulación mediante DFS con vector *discovery time* y *low-link* ($O(V+E)$).

---

## 5. Decisiones del Módulo 4: Distribución de Liquidez
- **Reducción a Flujo de Redes:** Super-fuente conectada a bóvedas centrales según su disponibilidad; super-sumidero conectado a agencias/ATM según su demanda de efectivo.
- **Algoritmo Principal:** Dinic con grafos de nivel (BFS) y bloqueo de caminos aumentantes (DFS) con punteros de avance (`work`), garantizando complejidad teórica $O(V^2 E)$.
- **Algoritmos de Comparación:** Edmonds-Karp ($O(V E^2)$) y Ford-Fulkerson clásico por DFS ($O(E \cdot f)$).
- **Corte Mínimo y Cuellos de Botella:** Identificación del corte a través de alcanzabilidad residual desde la super-fuente. Se analiza la ganancia marginal aumentando la capacidad en $\delta$ para priorizar inversiones de transporte.

---

## 6. Decisiones de Calidad y Entorno
- Principios de las skills `/file-organizer` y `/improve-codebase-architecture` aplicados estrictamente: arquitectura desacoplada, algoritmos puros en `src/algoritmos/` sin acoplamiento a modelos de negocio, módulos de orquestación en `src/`, y tests independientes con cobertura sobre oráculos de verificación.
