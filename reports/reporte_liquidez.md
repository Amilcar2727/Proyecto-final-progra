# Reporte de Planificación y Distribución de Liquidez hacia Bóvedas

## 1. Balance Financiero Global de Liquidez
- **Disponibilidad Total en Bóvedas:** `$3,500,000.00`
- **Demanda Total de Agencias/ATM:** `$1,945,000.00`
- **Efectivo Efectivamente Distribuido:** `$1,825,000.00`
- **Déficit Insatisfecho:** `$120,000.00`
- **Capacidad Teórica del Corte Mínimo:** `$1,825,000.00`
- **Teorema Max-Flow / Min-Cut Verificado:** `SÍ (Flujo == Capacidad Corte)`
- **Conservación de Flujo en Nodos Intermedios:** `VÁLIDA`
- **Respeto Estricto de Capacidades:** `VÁLIDO`

## 2. Nivel de Abastecimiento por Agencia / ATM
| Agencia / ATM | Demanda Requerida ($) | Efectivo Recibido ($) | Déficit ($) | Cumplimiento (%) |
|---|---|---|---|---|
| AG-ESTE-01 | $240,000.00 | $240,000.00 | $0.00 | 100.0% |
| AG-LIMA-01 | $350,000.00 | $350,000.00 | $0.00 | 100.0% |
| AG-LIMA-02 | $420,000.00 | $300,000.00 | $120,000.00 | 71.4% |
| AG-NORTE-01 | $280,000.00 | $280,000.00 | $0.00 | 100.0% |
| AG-NORTE-02 | $190,000.00 | $190,000.00 | $0.00 | 100.0% |
| AG-SUR-01 | $310,000.00 | $310,000.00 | $0.00 | 100.0% |
| ATM-LIMA-PLAZA | $50,000.00 | $50,000.00 | $0.00 | 100.0% |
| ATM-NORTE-MALL | $60,000.00 | $60,000.00 | $0.00 | 100.0% |
| ATM-SUR-CENTRO | $45,000.00 | $45,000.00 | $0.00 | 100.0% |

## 3. Despacho desde Bóvedas Centrales y Regionales
| Bóveda | Oferta Inicial ($) | Efectivo Despachado ($) | Remanente en Bóveda ($) | % Utilizado |
|---|---|---|---|---|
| BOVEDA-CENTRAL-BOGOTA | $1,500,000.00 | $430,000.00 | $1,070,000.00 | 28.7% |
| BOVEDA-CENTRAL-LIMA | $2,000,000.00 | $1,395,000.00 | $605,000.00 | 69.8% |

## 4. Cuellos de Botella Reales (Corte Mínimo) vs Rutas Saturadas No Críticas
> **Distinción Teórica Fundamental:** Una ruta puede alcanzar el 100% de su capacidad (estar saturada) sin ser cuello de botella del sistema si existen caminos alternativos redundantes con holgura. Por el contrario, las aristas del **Corte Mínimo** son las que limitan matemáticamente el flujo total global; ampliar cualquier otra ruta no aporta nada a la distribución global.

### Cuellos de Botella Reales (Pertenecen al Corte Mínimo)
- **REG-NORTE ➔ AG-LIMA-02**: Capacidad saturada `$300,000.00` (Limita el flujo de la red)

### Rutas Saturadas No Críticas (Fuera del Corte Mínimo)
- BOVEDA-CENTRAL-LIMA ➔ REG-NORTE: Capacidad `$800,000.00` saturada, pero no frena el flujo global.

## 5. Análisis de Sensibilidad y Priorización de Inversión Logística
Evaluación del impacto al aumentar la capacidad en **+$50,000.00** en cada cuello de botella:

| Prioridad | Ruta Cuello de Botella | Capacidad Actual ($) | Flujo Actual ($) | Ganancia Marginal ($) | Retorno Marginal de Inversión |
|---|---|---|---|---|---|
| **P-1** | REG-NORTE ➔ AG-LIMA-02 | $300,000.00 | $300,000.00 | **+$50,000.00** | 100.0% |
