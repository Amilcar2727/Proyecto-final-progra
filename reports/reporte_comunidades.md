# Reporte de Detección de Comunidades Financieras (Prevención de Fraude)

## 1. Resumen Ejecutivo del Algoritmo Louvain
- **Modularidad Global Q:** `0.5919`
- **Estabilidad Multi-Semilla:** `100.00%` de consistencia de pares
- **Comunidades Detectadas:** `11`
- **Nodos Concentradores Identificados:** `4`

### Nodos Concentradores Tratados
| Nodo ID | Grado | Tipo | Acción Aplicada |
|---|---|---|---|
| EMPRESA-CORP | 12 | cuenta | Concentrador con grado >= 7 (percentil 92.0%) |
| MUL-005 | 7 | cuenta | Concentrador con grado >= 7 (percentil 92.0%) |
| MUL-006 | 7 | cuenta | Concentrador con grado >= 7 (percentil 92.0%) |
| MUL-007 | 7 | cuenta | Concentrador con grado >= 7 (percentil 92.0%) |

## 2. Clasificación de Comunidades por Nivel de Prioridad de Auditoría
| ID | Cuentas | Densidad | Flujo Int / Ext | Vol. Total ($) | Score Prioridad | Cuentas Frontera |
|---|---|---|---|---|---|---|
| C-2 | 8 | 0.57 | 525.8 / 15.3 | $4,542,698.79 | **86.29** | Ninguna |
| C-1 | 3 | 1.00 | 138.0 / 0.0 | $19,329.62 | **69.87** | Ninguna |
| C-0 | 4 | 1.00 | 222.6 / 15.3 | $27,100.87 | **68.27** | Ninguna |
| C-5 | 2 | 1.00 | 14.2 / 0.0 | $1,215.18 | **67.10** | Ninguna |
| C-7 | 2 | 1.00 | 13.2 / 0.0 | $736.15 | **66.60** | Ninguna |
| C-9 | 2 | 1.00 | 12.9 / 0.0 | $620.17 | **66.43** | Ninguna |
| C-3 | 2 | 1.00 | 12.7 / 0.0 | $585.75 | **66.37** | Ninguna |
| C-4 | 1 | 0.00 | 0.0 / 0.0 | $0.00 | **0.00** | Ninguna |
| C-6 | 1 | 0.00 | 0.0 / 0.0 | $0.00 | **0.00** | Ninguna |
| C-8 | 1 | 0.00 | 0.0 / 0.0 | $0.00 | **0.00** | Ninguna |
| C-10 | 1 | 0.00 | 0.0 / 0.0 | $0.00 | **0.00** | Ninguna |

## 3. Desglose Explicable de Comunidades Prioritarias
### Comunidad C-2 (Score: 86.29/100)
- **Miembros:** `FAC-001, FAC-002, FAC-003, FAC-004, FAC-005, FAC-006, FAC-007, FAC-008`
- **Desglose de Factores:**
  - densidad: `17.14 pts`
  - ratio_interno: `29.15 pts`
  - sospechosas_previas: `25.00 pts`
  - volumen_log: `15.00 pts`
- **Transferencias Principales:**
  - FAC-001 ➔ FAC-004: $438,755.24 (3 transacciones)
  - FAC-002 ➔ FAC-003: $428,739.47 (4 transacciones)
  - FAC-001 ➔ FAC-005: $386,667.74 (3 transacciones)
  - FAC-001 ➔ FAC-008: $376,409.30 (4 transacciones)
  - FAC-005 ➔ FAC-007: $370,237.00 (3 transacciones)

### Comunidad C-1 (Score: 69.87/100)
- **Miembros:** `MUL-008, MUL-009, MUL-010`
- **Desglose de Factores:**
  - densidad: `30.00 pts`
  - ratio_interno: `30.00 pts`
  - sospechosas_previas: `0.00 pts`
  - volumen_log: `9.87 pts`
- **Transferencias Principales:**
  - MUL-008 ➔ MUL-009: $8,716.60 (3 transacciones)
  - MUL-008 ➔ MUL-010: $6,651.99 (6 transacciones)
  - MUL-009 ➔ MUL-010: $3,961.03 (7 transacciones)

### Comunidad C-0 (Score: 68.27/100)
- **Miembros:** `MUL-001, MUL-002, MUL-003, MUL-004`
- **Desglose de Factores:**
  - densidad: `30.00 pts`
  - ratio_interno: `28.06 pts`
  - sospechosas_previas: `0.00 pts`
  - volumen_log: `10.21 pts`
- **Transferencias Principales:**
  - MUL-001 ➔ MUL-003: $7,278.26 (3 transacciones)
  - MUL-002 ➔ MUL-004: $6,596.27 (6 transacciones)
  - MUL-002 ➔ MUL-003: $3,550.93 (7 transacciones)
  - MUL-003 ➔ MUL-004: $2,797.24 (5 transacciones)
  - MUL-001 ➔ MUL-004: $2,232.42 (3 transacciones)

### Comunidad C-5 (Score: 67.10/100)
- **Miembros:** `NOM-004, NOM-005`
- **Desglose de Factores:**
  - densidad: `30.00 pts`
  - ratio_interno: `30.00 pts`
  - sospechosas_previas: `0.00 pts`
  - volumen_log: `7.10 pts`
- **Transferencias Principales:**
  - NOM-004 ➔ NOM-005: $1,215.18 (2 transacciones)

### Comunidad C-7 (Score: 66.60/100)
- **Miembros:** `NOM-007, NOM-008`
- **Desglose de Factores:**
  - densidad: `30.00 pts`
  - ratio_interno: `30.00 pts`
  - sospechosas_previas: `0.00 pts`
  - volumen_log: `6.60 pts`
- **Transferencias Principales:**
  - NOM-007 ➔ NOM-008: $736.15 (2 transacciones)
