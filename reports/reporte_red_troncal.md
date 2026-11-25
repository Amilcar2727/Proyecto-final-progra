# Reporte de Optimización de Red Troncal Financiera (MST)

## 1. Resumen de Optimización y Costos
- **Costo Red Troncal Óptima (Kruskal):** `$74,785.70`
- **Costo Red Troncal Óptima (Prim):** `$74,785.70`
- **Costo Red Completa Candidata:** `$183,223.41`
- **Ahorro Financiero Obtenido:** `$108,437.71` (`59.18%`)
- **Componentes Conexas:** `1`
- **Total Enlaces Seleccionados:** `17`

## 2. Enlaces Troncales Seleccionados (Secuencia Kruskal)
| Paso | Origen | Destino | Costo Instalación ($) | Costo Operativo ($/mes) | Latencia (ms) | Costo Ponderado ($) |
|---|---|---|---|---|---|---|
| 1 | AG-004 | ATM-003 | $940.86 | $52.10 | 3.2 ms | $1,566.10 |
| 2 | AG-004 | ATM-004 | $815.82 | $120.78 | 1.2 ms | $2,265.23 |
| 3 | AG-004 | ATM-006 | $1,412.65 | $98.54 | 3.2 ms | $2,595.15 |
| 4 | AG-006 | ATM-002 | $1,763.82 | $101.76 | 1.5 ms | $2,984.91 |
| 5 | AG-001 | AG-008 | $1,612.35 | $133.63 | 4.1 ms | $3,215.88 |
| 6 | AG-004 | ATM-001 | $2,368.49 | $89.90 | 3.7 ms | $3,447.28 |
| 7 | AG-005 | AG-008 | $2,634.55 | $83.31 | 9.4 ms | $3,634.28 |
| 8 | AG-002 | ATM-005 | $2,791.92 | $135.96 | 1.3 ms | $4,423.49 |
| 9 | AG-002 | AG-005 | $2,363.20 | $175.43 | 4.1 ms | $4,468.39 |
| 10 | AG-004 | AG-007 | $3,252.05 | $110.37 | 9.3 ms | $4,576.50 |
| 11 | SEDE-REGIONAL-N | AG-006 | $2,472.80 | $187.95 | 10.5 ms | $4,728.24 |
| 12 | AG-004 | AG-006 | $3,021.68 | $157.13 | 9.6 ms | $4,907.27 |
| 13 | AG-002 | AG-004 | $3,794.04 | $147.26 | 9.3 ms | $5,561.12 |
| 14 | SEDE-CENTRAL | AG-001 | $5,032.13 | $107.96 | 5.4 ms | $6,327.66 |
| 15 | AG-003 | AG-009 | $4,022.53 | $195.89 | 6.3 ms | $6,373.22 |
| 16 | AG-007 | AG-009 | $4,553.52 | $151.93 | 3.7 ms | $6,376.72 |
| 17 | SEDE-REGIONAL-S | AG-002 | $4,517.12 | $234.76 | 6.3 ms | $7,334.27 |

## 3. Análisis de Fragilidad y Vulnerabilidad de la Red Troncal
- **Total Puntos de Articulación (Nodos Críticos):** `8`
- **Total Puentes Críticos (Enlaces Cuello de Botella):** `17`
- **Puntos de Articulación:** `AG-001, AG-002, AG-004, AG-005, AG-006, AG-007, AG-008, AG-009`

### Enlaces de Redundancia Recomendados (Menor Costo)
| Origen | Destino | Costo Proyectado ($) | Latencia (ms) | Protege Punto Crítico |
|---|---|---|---|---|
| SEDE-REGIONAL-N | AG-004 | $5,181.00 | 7.3 ms | Sí |
| AG-001 | AG-004 | $5,806.72 | 7.1 ms | Sí |
| AG-004 | AG-008 | $5,938.62 | 3.2 ms | Sí |
| AG-006 | AG-009 | $6,684.41 | 3.0 ms | Sí |
| AG-001 | AG-002 | $7,060.28 | 6.9 ms | Sí |
