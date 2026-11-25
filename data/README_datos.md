# Formato y Finalidad de los Datos de OptiFin

## Descripción General
Los archivos de datos son generados reproduciblemente mediante `python scripts/generar_datos.py --seed 42`.
Todos los timestamps están en formato ISO 8601.

---

## `transacciones.json` – Módulo 2 (Detección de Comunidades y Fraude)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Identificador único de cuenta bancaria |
| `tipo` | string | Tipo de nodo (`cuenta`, `cliente`) |
| `grupo_real` | string | Etiqueta de ground-truth (mulas, fachada, nomina) |
| `sospechoso` | bool | Si fue marcado previamente como sospechoso |
| `origen` | string | Cuenta emisora de la transferencia |
| `destino` | string | Cuenta receptora de la transferencia |
| `monto` | float | Monto total en USD de la arista agregada |
| `n_transferencias` | int | Número de transferencias individuales representadas |
| `timestamp` | string ISO | Fecha/hora de la última transferencia en la arista |
| `riesgo` | float [0,1] | Índice de riesgo transaccional |
| `canal` | string | Canal transaccional (app_movil, spei, swift) |

**Clusters inyectados:** mulas (10 cuentas), fachada (8 cuentas), nómina (12 cuentas).

---

## `red_troncal.json` – Módulo 3 (MST de Red Troncal)

| Campo | Tipo | Descripción |
|---|---|---|
| `costo_instalacion` | float | Costo de despliegue del enlace en USD |
| `costo_operativo` | float | Costo mensual de mantenimiento en USD |
| `tiempo` | float | Latencia del enlace en milisegundos |
| `disponible` | bool | Si el enlace puede ser seleccionado (False = prohibido) |
| `canal` | string | Tipo de enlace (fibra_optica, enlace_dedicado, vpn_sd_wan, enlace_ATM) |

**Criterio de peso MST por defecto:** `costo_instalacion + costo_operativo * 12 meses`.

---

## `distribucion_liquidez.json` – Módulo 4 (Flujo Máximo y Corte Mínimo)

| Campo | Tipo | Descripción |
|---|---|---|
| `capacidad` | float | Capacidad máxima de transporte en USD |
| `costo_unitario` | float | Costo por USD transportado |
| `disponibilidad_bovedas` | dict | Oferta de efectivo por bóveda central |
| `demanda_agencias` | dict | Demanda requerida de cada agencia y ATM |

**Cuello de botella intencional:** La arista `REG-NORTE -> AG-LIMA-02` tiene capacidad 300,000 USD
con una demanda de 420,000 USD, forzando restricción de flujo hacia ese destino.
