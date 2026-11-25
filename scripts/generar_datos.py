"""
Generador reproducible de datos sintéticos para OptiFin.
Produce datasets realistas para los tres escenarios:
  - transacciones.json  (Módulo 2: comunidades y fraude)
  - red_troncal.json    (Módulo 3: MST de red troncal)
  - distribucion_liquidez.json (Módulo 4: flujo máximo y corte mínimo)
Uso:
    python scripts/generar_datos.py [--seed 42]
"""

from __future__ import annotations
import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta

# Asegurar que el módulo raíz sea encontrado
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def generar_transacciones(seed: int = 42, n_cuentas: int = 40) -> dict:
    """
    Genera una red de transacciones financieras con 3 comunidades inyectadas:
    - Grupo A: Cluster sospechoso de estructuración (smurfing)
    - Grupo B: Cluster de empresas de fachada con volumen alto
    - Grupo C: Red de cuentas legítimas conectadas por pagos de nómina
    """
    rng = random.Random(seed)
    hoy = datetime(2026, 11, 25)

    nodos = []
    aristas = []

    # Cluster A: Mulas (10 cuentas, transferencias pequeñas y frecuentes)
    cuentas_mulas = [f"MUL-{i:03d}" for i in range(1, 11)]
    for cta in cuentas_mulas:
        nodos.append({"id": cta, "tipo": "cuenta", "atributos": {"grupo_real": "mulas", "sospechoso": False}})

    # Aristas internas mulas (monto bajo, frecuencia alta)
    for i in range(len(cuentas_mulas)):
        for j in range(i + 1, min(i + 4, len(cuentas_mulas))):
            dias = rng.randint(0, 29)
            ts = (hoy - timedelta(days=dias)).isoformat()
            n = rng.randint(3, 8)
            aristas.append({
                "origen": cuentas_mulas[i],
                "destino": cuentas_mulas[j],
                "monto": rng.uniform(2000.0, 9800.0),
                "n_transferencias": n,
                "timestamp": ts,
                "comision": rng.uniform(0.1, 0.5) * n,
                "riesgo": rng.uniform(0.4, 0.75),
                "disponible": True,
                "canal": "app_movil",
            })

    # Cluster B: Empresas de fachada (8 cuentas, montos altos irregulares)
    cuentas_fachada = [f"FAC-{i:03d}" for i in range(1, 9)]
    for cta in cuentas_fachada:
        nodos.append({"id": cta, "tipo": "cuenta", "atributos": {"grupo_real": "fachada", "sospechoso": True}})

    for i in range(len(cuentas_fachada)):
        for j in range(i + 1, len(cuentas_fachada)):
            if rng.random() < 0.6:
                dias = rng.randint(0, 29)
                ts = (hoy - timedelta(days=dias)).isoformat()
                n = rng.randint(1, 4)
                aristas.append({
                    "origen": cuentas_fachada[i],
                    "destino": cuentas_fachada[j],
                    "monto": rng.uniform(50000.0, 450000.0),
                    "n_transferencias": n,
                    "timestamp": ts,
                    "comision": rng.uniform(5.0, 50.0),
                    "riesgo": rng.uniform(0.6, 0.95),
                    "disponible": True,
                    "canal": "swift",
                })

    # Cluster C: Cuentas de nómina legítimas (12 cuentas)
    cuentas_nomina = [f"NOM-{i:03d}" for i in range(1, 13)]
    for cta in cuentas_nomina:
        nodos.append({"id": cta, "tipo": "cliente", "atributos": {"grupo_real": "nomina", "sospechoso": False}})

    # Empresa pagadora como concentradora
    nodos.append({"id": "EMPRESA-CORP", "tipo": "cuenta", "atributos": {"grupo_real": "concentrador", "sospechoso": False}})

    for cta in cuentas_nomina:
        dias = rng.randint(0, 5)  # Pago reciente de nómina
        ts = (hoy - timedelta(days=dias)).isoformat()
        aristas.append({
            "origen": "EMPRESA-CORP",
            "destino": cta,
            "monto": rng.uniform(3500.0, 12000.0),
            "n_transferencias": 1,
            "timestamp": ts,
            "comision": 1.5,
            "riesgo": 0.02,
            "disponible": True,
            "canal": "spei",
        })

    # Algunas transferencias entre cuentas de nómina
    for i in range(0, len(cuentas_nomina) - 1, 3):
        dias = rng.randint(0, 20)
        ts = (hoy - timedelta(days=dias)).isoformat()
        aristas.append({
            "origen": cuentas_nomina[i],
            "destino": cuentas_nomina[i + 1],
            "monto": rng.uniform(500.0, 2000.0),
            "n_transferencias": 2,
            "timestamp": ts,
            "comision": 1.0,
            "riesgo": 0.03,
            "disponible": True,
            "canal": "app_movil",
        })

    # Vínculos débiles entre clusters (simular ruido y conexiones frontera)
    for _ in range(5):
        orig = rng.choice(cuentas_mulas)
        dest = rng.choice(cuentas_fachada)
        dias = rng.randint(0, 29)
        ts = (hoy - timedelta(days=dias)).isoformat()
        aristas.append({
            "origen": orig,
            "destino": dest,
            "monto": rng.uniform(1000.0, 5000.0),
            "n_transferencias": 1,
            "timestamp": ts,
            "comision": 0.5,
            "riesgo": rng.uniform(0.3, 0.6),
            "disponible": True,
            "canal": "app_movil",
        })

    return {
        "descripcion": "Red de transacciones financieras con clusters de fraude inyectados - OptiFin Módulo 2",
        "semilla_generacion": seed,
        "dirigido": True,
        "ponderado": True,
        "nodos": nodos,
        "aristas": aristas,
    }


def generar_red_troncal(seed: int = 42) -> dict:
    """
    Genera una red de infraestructura financiera con nodos tipo sede, agencia y ATM.
    Algunos enlaces no están disponibles para simular restricciones operativas.
    """
    rng = random.Random(seed)

    sedes = [
        {"id": "SEDE-CENTRAL", "tipo": "entidad", "atributos": {"ciudad": "Lima", "region": "Centro"}},
        {"id": "SEDE-REGIONAL-N", "tipo": "entidad", "atributos": {"ciudad": "Trujillo", "region": "Norte"}},
        {"id": "SEDE-REGIONAL-S", "tipo": "entidad", "atributos": {"ciudad": "Arequipa", "region": "Sur"}},
    ]
    agencias = [
        {"id": f"AG-{i:03d}", "tipo": "agencia", "atributos": {"ciudad": f"Ciudad-{i}", "region": rng.choice(["Norte", "Sur", "Centro"])}}
        for i in range(1, 10)
    ]
    atms = [
        {"id": f"ATM-{i:03d}", "tipo": "atm", "atributos": {"ubicacion": f"Plaza-{i}"}}
        for i in range(1, 7)
    ]

    nodos = sedes + agencias + atms
    todos_ids = [n["id"] for n in nodos]

    aristas = []

    # Conexiones sede central -> regionales
    for sede in sedes[1:]:
        aristas.append({
            "origen": "SEDE-CENTRAL",
            "destino": sede["id"],
            "costo_instalacion": rng.uniform(5000.0, 15000.0),
            "costo_operativo": rng.uniform(300.0, 800.0),
            "tiempo": rng.uniform(5.0, 20.0),
            "disponible": True,
            "canal": "fibra_optica",
        })

    # Conexiones sedes -> agencias
    for ag in agencias:
        sede_asignada = rng.choice([s["id"] for s in sedes])
        aristas.append({
            "origen": sede_asignada,
            "destino": ag["id"],
            "costo_instalacion": rng.uniform(2000.0, 8000.0),
            "costo_operativo": rng.uniform(100.0, 400.0),
            "tiempo": rng.uniform(3.0, 15.0),
            "disponible": rng.random() > 0.1,  # 10% no disponibles
            "canal": "enlace_dedicado",
        })

    # Conexiones agencias entre sí (candidatas adicionales)
    ag_ids = [a["id"] for a in agencias]
    for i in range(len(ag_ids)):
        for j in range(i + 1, len(ag_ids)):
            if rng.random() < 0.35:
                aristas.append({
                    "origen": ag_ids[i],
                    "destino": ag_ids[j],
                    "costo_instalacion": rng.uniform(1500.0, 5000.0),
                    "costo_operativo": rng.uniform(80.0, 250.0),
                    "tiempo": rng.uniform(2.0, 10.0),
                    "disponible": rng.random() > 0.15,
                    "canal": "vpn_sd_wan",
                })

    # Conexiones agencias -> ATMs
    for atm in atms:
        ag_cercana = rng.choice(ag_ids)
        aristas.append({
            "origen": ag_cercana,
            "destino": atm["id"],
            "costo_instalacion": rng.uniform(800.0, 3000.0),
            "costo_operativo": rng.uniform(50.0, 150.0),
            "tiempo": rng.uniform(1.0, 5.0),
            "disponible": True,
            "canal": "enlace_ATM",
        })

    return {
        "descripcion": "Red de infraestructura de conectividad para la red troncal financiera - OptiFin Módulo 3",
        "semilla_generacion": seed,
        "dirigido": False,
        "ponderado": True,
        "nodos": nodos,
        "aristas": aristas,
    }


def generar_distribucion_liquidez(seed: int = 42) -> dict:
    """
    Genera una red de distribución de efectivo con bóvedas, rutas de transporte y demandas.
    Incluye intencionalmente un cuello de botella para validar el Módulo 4.
    """
    rng = random.Random(seed)

    nodos = [
        {"id": "BOVEDA-CENTRAL-LIMA", "tipo": "boveda_central", "atributos": {"oferta": 2000000.0, "region": "Lima"}},
        {"id": "BOVEDA-CENTRAL-BOGOTA", "tipo": "boveda_central", "atributos": {"oferta": 1500000.0, "region": "Bogota"}},
        {"id": "REG-NORTE", "tipo": "boveda_regional", "atributos": {"region": "Norte"}},
        {"id": "REG-SUR", "tipo": "boveda_regional", "atributos": {"region": "Sur"}},
        {"id": "REG-ESTE", "tipo": "boveda_regional", "atributos": {"region": "Este"}},
    ]

    agencias = [
        {"id": "AG-LIMA-01", "tipo": "agencia", "atributos": {"demanda": 350000.0, "ciudad": "Lima-Centro"}},
        {"id": "AG-LIMA-02", "tipo": "agencia", "atributos": {"demanda": 420000.0, "ciudad": "Lima-Norte"}},
        {"id": "AG-NORTE-01", "tipo": "agencia", "atributos": {"demanda": 280000.0, "ciudad": "Trujillo"}},
        {"id": "AG-NORTE-02", "tipo": "agencia", "atributos": {"demanda": 190000.0, "ciudad": "Chiclayo"}},
        {"id": "AG-SUR-01", "tipo": "agencia", "atributos": {"demanda": 310000.0, "ciudad": "Arequipa"}},
        {"id": "AG-ESTE-01", "tipo": "agencia", "atributos": {"demanda": 240000.0, "ciudad": "Cusco"}},
    ]
    atms = [
        {"id": "ATM-LIMA-PLAZA", "tipo": "atm", "atributos": {"demanda": 50000.0}},
        {"id": "ATM-NORTE-MALL", "tipo": "atm", "atributos": {"demanda": 60000.0}},
        {"id": "ATM-SUR-CENTRO", "tipo": "atm", "atributos": {"demanda": 45000.0}},
    ]

    nodos += agencias + atms

    aristas = [
        # Central Lima -> Regionales
        {"origen": "BOVEDA-CENTRAL-LIMA", "destino": "REG-NORTE", "capacidad": 800000.0, "costo_unitario": 0.001, "disponible": True, "canal": "blindado"},
        {"origen": "BOVEDA-CENTRAL-LIMA", "destino": "REG-SUR", "capacidad": 700000.0, "costo_unitario": 0.0012, "disponible": True, "canal": "blindado"},
        {"origen": "BOVEDA-CENTRAL-LIMA", "destino": "REG-ESTE", "capacidad": 600000.0, "costo_unitario": 0.0015, "disponible": True, "canal": "blindado"},
        # Central Bogota -> Regionales
        {"origen": "BOVEDA-CENTRAL-BOGOTA", "destino": "REG-NORTE", "capacidad": 500000.0, "costo_unitario": 0.0014, "disponible": True, "canal": "blindado"},
        # REG-NORTE -> Agencias y ATMs
        {"origen": "REG-NORTE", "destino": "AG-LIMA-01", "capacidad": 400000.0, "costo_unitario": 0.0008, "disponible": True, "canal": "blindado_local"},
        {"origen": "REG-NORTE", "destino": "AG-LIMA-02", "capacidad": 300000.0, "costo_unitario": 0.0009, "disponible": True, "canal": "blindado_local"},  # <-- cuello de botella intencional
        {"origen": "REG-NORTE", "destino": "AG-NORTE-01", "capacidad": 350000.0, "costo_unitario": 0.001, "disponible": True, "canal": "blindado_local"},
        {"origen": "REG-NORTE", "destino": "AG-NORTE-02", "capacidad": 250000.0, "costo_unitario": 0.0011, "disponible": True, "canal": "blindado_local"},
        {"origen": "REG-NORTE", "destino": "ATM-NORTE-MALL", "capacidad": 80000.0, "costo_unitario": 0.0005, "disponible": True, "canal": "remesa"},
        # REG-SUR -> Agencias y ATMs
        {"origen": "REG-SUR", "destino": "AG-SUR-01", "capacidad": 400000.0, "costo_unitario": 0.001, "disponible": True, "canal": "blindado_local"},
        {"origen": "REG-SUR", "destino": "ATM-SUR-CENTRO", "capacidad": 60000.0, "costo_unitario": 0.0005, "disponible": True, "canal": "remesa"},
        # REG-ESTE -> Agencias
        {"origen": "REG-ESTE", "destino": "AG-ESTE-01", "capacidad": 300000.0, "costo_unitario": 0.0013, "disponible": True, "canal": "blindado_local"},
        # ATMs Lima desde NORTE
        {"origen": "REG-NORTE", "destino": "ATM-LIMA-PLAZA", "capacidad": 70000.0, "costo_unitario": 0.0005, "disponible": True, "canal": "remesa"},
    ]

    disponibilidad = {
        "BOVEDA-CENTRAL-LIMA": 2000000.0,
        "BOVEDA-CENTRAL-BOGOTA": 1500000.0,
    }
    demanda = {ag["id"]: ag["atributos"]["demanda"] for ag in agencias}
    demanda.update({atm["id"]: atm["atributos"]["demanda"] for atm in atms})

    return {
        "descripcion": "Red de distribución de efectivo con cuello de botella intencional - OptiFin Módulo 4",
        "semilla_generacion": seed,
        "dirigido": True,
        "ponderado": True,
        "disponibilidad_bovedas": disponibilidad,
        "demanda_agencias": demanda,
        "nodos": nodos,
        "aristas": aristas,
    }


def main():
    parser = argparse.ArgumentParser(description="Generador de datos sintéticos para OptiFin")
    parser.add_argument("--seed", type=int, default=42, help="Semilla de aleatoriedad (por defecto: 42)")
    args = parser.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    print(f"[OptiFin] Generando datos con semilla: {args.seed}")

    datasets = {
        "transacciones.json": generar_transacciones(seed=args.seed),
        "red_troncal.json": generar_red_troncal(seed=args.seed),
        "distribucion_liquidez.json": generar_distribucion_liquidez(seed=args.seed),
    }

    for nombre, datos in datasets.items():
        ruta = os.path.join(data_dir, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"  [OK] {ruta}  ({len(datos.get('nodos', []))} nodos, {len(datos.get('aristas', []))} aristas)")

    print(f"\n[OptiFin] Datos generados correctamente en '{data_dir}'.")


if __name__ == "__main__":
    main()
