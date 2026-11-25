"""
OptiFin – Sistema de Análisis y Optimización de Redes Financieras.
Punto de entrada principal. Soporta modo interactivo (menú terminal) y no interactivo
(--demo, --modulo N, --datos RUTA).

Uso:
    python main.py                           # Menú interactivo
    python main.py --demo                    # Ejecuta demo completa de los 3 módulos
    python main.py --modulo 2                # Ejecuta solo el Módulo 2 con datos por defecto
    python main.py --modulo 3 --datos data/red_troncal.json
    python main.py --modulo 4 --datos data/distribucion_liquidez.json
    python main.py --benchmark               # Ejecuta benchmarks de rendimiento
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from typing import Optional

# Asegurar raíz en PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.analisis_transacciones import AnalizadorTransaccionesFinancieras
from src.distribucion_liquidez import PlanificadorDistribucionLiquidez
from src.enrutamiento_financiero import OptimizadorRedTroncal
from src.evaluacion_resultados import EvaluadorResultados
from src.gestion_red import ErrorArchivoInvalido, ErrorValidacionRed, GestorRedFinanciera
from src.graph import Edge, Graph, Node
from src.utils import fijar_semilla


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          OptiFin – Análisis y Optimización de Redes          ║
║                     Financieras v1.0                         ║
║         Programación III | Teoría de Grafos Aplicada         ║
╚══════════════════════════════════════════════════════════════╝
"""

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def asegurar_datos() -> None:
    """Genera los datos sintéticos si no existen todavía."""
    archivos = ["transacciones.json", "red_troncal.json", "distribucion_liquidez.json"]
    faltan = [a for a in archivos if not os.path.exists(os.path.join(DATA_DIR, a))]
    if faltan:
        print("[OptiFin] Generando datos sintéticos de demostración...")
        import subprocess
        subprocess.run([sys.executable, "scripts/generar_datos.py"], check=True)


# ─────────────────────────────────────────────────────────────────────────────
#  MÓDULO 2 – DETECCIÓN DE COMUNIDADES (FRAUDE)
# ─────────────────────────────────────────────────────────────────────────────

def cargar_grafo_json(ruta: str, dirigido: bool = True) -> Graph:
    """Carga un grafo desde JSON con validación de errores detallada."""
    gestor = GestorRedFinanciera()
    try:
        return gestor.cargar_desde_json(ruta, estricto=False)
    except (ErrorArchivoInvalido, ErrorValidacionRed) as e:
        print(f"[ERROR] No se pudo cargar '{ruta}': {e}")
        sys.exit(1)


def ejecutar_modulo2(datos: Optional[str] = None, interactivo: bool = True) -> None:
    ruta = datos or os.path.join(DATA_DIR, "transacciones.json")
    print(f"\n{'━'*62}")
    print("  MÓDULO 2: Detección de Comunidades para Prevención de Fraude")
    print(f"{'━'*62}")
    print(f"  Fuente de datos: {ruta}")

    grafo = cargar_grafo_json(ruta)
    print(f"  Red cargada: {grafo.num_nodos} nodos, {grafo.num_aristas} aristas")

    analizador = AnalizadorTransaccionesFinancieras(
        criterio_peso="combinado",
        ventana_dias=30,
        percentil_concentrador=92.0,
    )

    if interactivo:
        print("\n  ┌─ Configuración (Enter = usar valor por defecto) ─────────┐")
        try:
            n_corridas_str = input("  │  N° corridas Louvain [5]: ").strip()
            n_corridas = int(n_corridas_str) if n_corridas_str else 5
            umbral_str = input("  │  Umbral de peso para línea base [3.0]: ").strip()
            umbral = float(umbral_str) if umbral_str else 3.0
        except (ValueError, KeyboardInterrupt):
            n_corridas, umbral = 5, 3.0
        print("  └──────────────────────────────────────────────────────────┘")
    else:
        n_corridas, umbral = 5, 3.0

    print("\n  [1/4] Preprocesando red...")
    t0 = time.perf_counter()
    g_prep = analizador.preprocesar_red(grafo, accion_concentrador="excluir")
    print(f"  → Red preprocesada: {g_prep.num_nodos} nodos ({grafo.num_nodos - g_prep.num_nodos} concentradores excluidos)")

    print("\n  [2/4] Ejecutando Louvain (multisemilla)...")
    res_louvain = analizador.detectar_comunidades_louvain(g_prep, n_corridas=n_corridas, semilla=42)
    metricas = analizador.analizar_comunidades(g_prep, res_louvain["particion"])

    print("\n  [3/4] Ejecutando líneas base (Umbral + LPA)...")
    lineas_base = analizador.detectar_lineas_base(g_prep, umbral_peso=umbral, semilla=42)

    print("\n  [4/4] Generando reportes...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ruta_rep = os.path.join(REPORTS_DIR, "reporte_comunidades.md")
    md = analizador.generar_reporte_markdown(
        metricas, res_louvain["modularidad"], res_louvain["estabilidad"], ruta_salida=ruta_rep
    )

    t1 = time.perf_counter()

    print(f"\n  ┌─ RESULTADOS ──────────────────────────────────────────────")
    print(f"  │  Modularidad Louvain:   Q = {res_louvain['modularidad']:.4f}")
    print(f"  │  Estabilidad:               {res_louvain['estabilidad']*100:.1f}%")
    print(f"  │  Comunidades detectadas:    {len(metricas)}")
    print(f"  │  Modularidad LPA:       Q = {lineas_base['lpa']['modularidad']:.4f}")
    print(f"  │  Modularidad Umbral {umbral}:  Q = {lineas_base['umbral']['modularidad']:.4f}")
    print(f"  │  Tiempo total:              {(t1-t0)*1000:.1f} ms")
    print(f"  └───────────────────────────────────────────────────────────")
    print(f"\n  Comunidades (ordenadas por prioridad de auditoría):")
    for m in metricas[:6]:
        indicador = "🔴" if m.puntaje_prioridad > 50 else "🟡" if m.puntaje_prioridad > 25 else "🟢"
        print(f"  {indicador}  C-{m.id_comunidad}: {m.tamano} cuentas | densidad {m.densidad_interna:.2f} | score {m.puntaje_prioridad:.1f}")
    print(f"\n  → Reporte completo guardado en: {ruta_rep}")


# ─────────────────────────────────────────────────────────────────────────────
#  MÓDULO 3 – RED TRONCAL (MST)
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_modulo3(datos: Optional[str] = None, interactivo: bool = True) -> None:
    ruta = datos or os.path.join(DATA_DIR, "red_troncal.json")
    print(f"\n{'━'*62}")
    print("  MÓDULO 3: Diseño de Red Troncal de Menor Costo (MST)")
    print(f"{'━'*62}")
    print(f"  Fuente de datos: {ruta}")

    grafo = cargar_grafo_json(ruta, dirigido=False)
    print(f"  Red cargada: {grafo.num_nodos} nodos, {grafo.num_aristas} aristas")

    if interactivo:
        print("\n  ┌─ Configuración (Enter = valor por defecto) ───────────────┐")
        try:
            horizonte_str = input("  │  Horizonte operativo en meses [12]: ").strip()
            horizonte = float(horizonte_str) if horizonte_str else 12.0
            alpha_str = input("  │  Factor α (peso del costo) [1.0]: ").strip()
            alpha = float(alpha_str) if alpha_str else 1.0
            beta_str = input("  │  Factor β (peso de latencia) [0.0]: ").strip()
            beta = float(beta_str) if beta_str else 0.0
        except (ValueError, KeyboardInterrupt):
            horizonte, alpha, beta = 12.0, 1.0, 0.0
        print("  └──────────────────────────────────────────────────────────┘")
    else:
        horizonte, alpha, beta = 12.0, 1.0, 0.0

    optimizador = OptimizadorRedTroncal(horizonte_meses=horizonte, alpha_costo=alpha, beta_latencia=beta)

    print("\n  [1/3] Ejecutando Kruskal + Union-Find...")
    t0 = time.perf_counter()
    res_k = optimizador.ejecutar_kruskal(grafo)
    t_k = time.perf_counter() - t0

    print("  [2/3] Ejecutando Prim + Min-Heap...")
    t0 = time.perf_counter()
    res_p = optimizador.ejecutar_prim(grafo)
    t_p = time.perf_counter() - t0

    print("  [3/3] Analizando fragilidad y ahorro...")
    fragilidad = optimizador.analizar_fragilidad(grafo, res_k)
    ahorro = optimizador.calcular_ahorro_economico(grafo, res_k)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    ruta_rep = os.path.join(REPORTS_DIR, "reporte_red_troncal.md")
    md = optimizador.generar_reporte_markdown(res_k, res_p, fragilidad, ahorro, ruta_salida=ruta_rep)

    print(f"\n  ┌─ RESULTADOS ──────────────────────────────────────────────")
    print(f"  │  Costo Red Troncal (Kruskal): ${res_k.peso_total:>14,.2f}")
    print(f"  │  Costo Red Troncal (Prim):    ${res_p.peso_total:>14,.2f}")
    print(f"  │  Ahorro vs. red completa:     ${ahorro['ahorro_absoluto']:>14,.2f} ({ahorro['porcentaje_ahorro']:.1f}%)")
    print(f"  │  Componentes conectadas:       {res_k.num_componentes}")
    print(f"  │  Puentes críticos:             {fragilidad['total_puentes']}")
    print(f"  │  Puntos de articulación:       {fragilidad['total_articulaciones']}")
    print(f"  │  Tiempo Kruskal:               {t_k*1000:.2f} ms")
    print(f"  │  Tiempo Prim:                  {t_p*1000:.2f} ms")
    print(f"  └───────────────────────────────────────────────────────────")

    if interactivo:
        try:
            consulta = input("\n  ¿Consultar ruta en la red troncal? (orig dest / Enter para omitir): ").strip()
            if consulta:
                partes = consulta.split()
                if len(partes) == 2:
                    info = optimizador.consultar_ruta_troncal(grafo, res_k, partes[0], partes[1])
                    if info["camino_mst"]:
                        print(f"\n  Camino: {' → '.join(info['camino_mst'])}")
                        print(f"  Costo acumulado: ${info['costo_mst']:,.2f} | Latencia: {info['latencia_mst']:.1f} ms")
                    else:
                        print("  Sin camino en la red troncal (posiblemente red desconectada).")
        except (ValueError, KeyboardInterrupt):
            pass

    print(f"\n  → Reporte completo guardado en: {ruta_rep}")


# ─────────────────────────────────────────────────────────────────────────────
#  MÓDULO 4 – DISTRIBUCIÓN DE LIQUIDEZ
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_modulo4(datos: Optional[str] = None, interactivo: bool = True) -> None:
    ruta = datos or os.path.join(DATA_DIR, "distribucion_liquidez.json")
    print(f"\n{'━'*62}")
    print("  MÓDULO 4: Distribución de Liquidez – Cuellos de Botella")
    print(f"{'━'*62}")
    print(f"  Fuente de datos: {ruta}")

    with open(ruta, encoding="utf-8") as f:
        datos_cargados = json.load(f)

    # Cargar grafo y metadatos de demanda/oferta
    gestor = GestorRedFinanciera()
    grafo = gestor.cargar_desde_json(ruta, estricto=False)

    disponibilidad = datos_cargados.get("disponibilidad_bovedas", {})
    demanda = datos_cargados.get("demanda_agencias", {})

    print(f"  Red cargada: {grafo.num_nodos} nodos, {grafo.num_aristas} aristas")
    print(f"  Oferta total disponible:  ${sum(disponibilidad.values()):>14,.2f}")
    print(f"  Demanda total requerida:  ${sum(demanda.values()):>14,.2f}")

    if interactivo:
        try:
            delta_str = input("\n  Δ para análisis de sensibilidad [50000.0]: ").strip()
            delta = float(delta_str) if delta_str else 50000.0
        except (ValueError, KeyboardInterrupt):
            delta = 50000.0
    else:
        delta = 50000.0

    planificador = PlanificadorDistribucionLiquidez(delta_sensibilidad=delta)

    print("\n  [1/4] Calculando flujo máximo con Dinic...")
    t0 = time.perf_counter()
    res_dinic = planificador.optimizar_flujo_dinic(grafo, disponibilidad, demanda)
    t_dinic = time.perf_counter() - t0

    print("  [2/4] Calculando flujo máximo con Edmonds-Karp...")
    t0 = time.perf_counter()
    res_ek = planificador.optimizar_flujo_edmonds_karp(grafo, disponibilidad, demanda)
    t_ek = time.perf_counter() - t0

    print("  [3/4] Calculando flujo máximo con Ford-Fulkerson...")
    t0 = time.perf_counter()
    res_ff = planificador.optimizar_flujo_ford_fulkerson(grafo, disponibilidad, demanda)
    t_ff = time.perf_counter() - t0

    print("  [4/4] Analizando sensibilidad de cuellos de botella...")
    sensibilidad = planificador.analizar_sensibilidad_cuellos_botella(grafo, disponibilidad, demanda, res_dinic)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    ruta_rep = os.path.join(REPORTS_DIR, "reporte_liquidez.md")
    md = planificador.generar_reporte_distribucion(grafo, disponibilidad, demanda, res_dinic, sensibilidad, ruta_rep)

    max_cut_check = "✓ VERIFICADO" if abs(res_dinic.flujo_maximo - res_dinic.capacidad_corte) < 0.01 else "✗ DISCREPANCIA"

    print(f"\n  ┌─ RESULTADOS ──────────────────────────────────────────────")
    print(f"  │  Flujo Máximo (Dinic):         ${res_dinic.flujo_maximo:>14,.2f}")
    print(f"  │  Flujo Máximo (Edmonds-Karp):  ${res_ek.flujo_maximo:>14,.2f}")
    print(f"  │  Flujo Máximo (Ford-Fulkerson):${res_ff.flujo_maximo:>14,.2f}")
    print(f"  │  Capacidad del Corte Mínimo:   ${res_dinic.capacidad_corte:>14,.2f}")
    print(f"  │  Teorema Max-Flow/Min-Cut:      {max_cut_check}")
    print(f"  │  Déficit de Liquidez:           ${(sum(demanda.values()) - res_dinic.flujo_maximo):>14,.2f}")
    print(f"  │  Cuellos de Botella Reales:     {len([c for c in res_dinic.cuellos_de_botella if '_SUPER_' not in c[0] and '_SUPER_' not in c[1]])}")
    print(f"  │  Tiempo Dinic:                  {t_dinic*1000:.2f} ms")
    print(f"  │  Tiempo Edmonds-Karp:           {t_ek*1000:.2f} ms")
    print(f"  │  Tiempo Ford-Fulkerson:         {t_ff*1000:.2f} ms")
    print(f"  └───────────────────────────────────────────────────────────")

    if sensibilidad:
        print(f"\n  Prioridades de Inversión (top {min(3, len(sensibilidad))}):")
        for idx, s in enumerate(sensibilidad[:3], 1):
            print(f"  P{idx}: {s.origen} → {s.destino} | Ganancia: +${s.ganancia_marginal:,.0f}")

    print(f"\n  → Reporte completo guardado en: {ruta_rep}")


# ─────────────────────────────────────────────────────────────────────────────
#  BENCHMARKS
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_benchmarks() -> None:
    print(f"\n{'━'*62}")
    print("  EVALUACIÓN DE RENDIMIENTO Y ESCALABILIDAD")
    print(f"{'━'*62}")
    evaluador = EvaluadorResultados(seed=42)

    print("\n  [1/2] Benchmarks de Árbol de Expansión Mínima (MST)...")
    reg_mst = evaluador.benchmark_mst(tamanos=[50, 200, 500], repeticiones=2, densidad="dispersa")

    print(f"\n  {'Algoritmo':<14} {'Nodos':>6} {'Aristas':>7} {'Tiempo (ms)':>12} {'Mem (KB)':>10}")
    print(f"  {'─'*55}")
    for r in reg_mst:
        print(f"  {r.algoritmo:<14} {r.nodos_v:>6} {r.aristas_e:>7} {r.tiempo_medio_seg*1000:>11.2f} {r.memoria_pico_kb:>9.1f}")

    print("\n  [2/2] Benchmarks de Flujo Máximo...")
    reg_flujo = evaluador.benchmark_flujo(tamanos=[50, 150, 300], repeticiones=2)

    print(f"\n  {'Algoritmo':<16} {'Nodos':>6} {'Aristas':>7} {'Tiempo (ms)':>12} {'Flujo':>12}")
    print(f"  {'─'*58}")
    for r in reg_flujo:
        print(f"  {r.algoritmo:<16} {r.nodos_v:>6} {r.aristas_e:>7} {r.tiempo_medio_seg*1000:>11.2f} {r.metrica_calidad:>12.0f}")


# ─────────────────────────────────────────────────────────────────────────────
#  MENÚ INTERACTIVO
# ─────────────────────────────────────────────────────────────────────────────

def menu_principal() -> None:
    print(BANNER)
    asegurar_datos()

    while True:
        print("\n  ┌─ MENÚ PRINCIPAL ────────────────────────────────────────┐")
        print("  │  1. Módulo 2: Detección de Comunidades (Fraude/Lavado)  │")
        print("  │  2. Módulo 3: Red Troncal de Menor Costo (MST)          │")
        print("  │  3. Módulo 4: Distribución de Liquidez (Flujo Máximo)   │")
        print("  │  4. Evaluación: Benchmarks de Rendimiento               │")
        print("  │  5. Demo Completa (todos los módulos)                   │")
        print("  │  6. Generar nuevos datos (semilla personalizada)        │")
        print("  │  0. Salir                                               │")
        print("  └─────────────────────────────────────────────────────────┘")

        try:
            opcion = input("  Seleccione una opción [0-6]: ").strip()
        except KeyboardInterrupt:
            print("\n\n  [OptiFin] Sesión terminada por el usuario. ¡Hasta pronto!")
            sys.exit(0)

        if opcion == "1":
            ejecutar_modulo2(interactivo=True)
        elif opcion == "2":
            ejecutar_modulo3(interactivo=True)
        elif opcion == "3":
            ejecutar_modulo4(interactivo=True)
        elif opcion == "4":
            ejecutar_benchmarks()
        elif opcion == "5":
            ejecutar_modulo2(interactivo=False)
            ejecutar_modulo3(interactivo=False)
            ejecutar_modulo4(interactivo=False)
        elif opcion == "6":
            try:
                seed_str = input("  Semilla de aleatoriedad [42]: ").strip()
                seed = int(seed_str) if seed_str else 42
            except ValueError:
                seed = 42
            import subprocess
            subprocess.run([sys.executable, "scripts/generar_datos.py", "--seed", str(seed)], check=True)
        elif opcion == "0":
            print("\n  [OptiFin] Sesión finalizada. ¡Hasta pronto!")
            sys.exit(0)
        else:
            print("  Opción no válida. Ingrese un número del 0 al 6.")


# ─────────────────────────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    fijar_semilla(42)

    parser = argparse.ArgumentParser(
        description="OptiFin – Sistema de Análisis y Optimización de Redes Financieras",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                                 # Menú interactivo
  python main.py --demo                          # Demo completa
  python main.py --modulo 2                      # Solo Módulo 2 con datos por defecto
  python main.py --modulo 3 --datos data/red_troncal.json
  python main.py --modulo 4 --datos data/distribucion_liquidez.json
  python main.py --benchmark                     # Benchmarks de rendimiento
        """,
    )
    parser.add_argument("--demo", action="store_true", help="Ejecutar demo completa de todos los módulos")
    parser.add_argument("--modulo", type=int, choices=[2, 3, 4], help="Número del módulo a ejecutar (2, 3 o 4)")
    parser.add_argument("--datos", type=str, help="Ruta al archivo de datos (.json o .csv)")
    parser.add_argument("--benchmark", action="store_true", help="Ejecutar benchmarks de rendimiento")
    parser.add_argument("--seed", type=int, default=42, help="Semilla de aleatoriedad (defecto: 42)")

    args = parser.parse_args()
    fijar_semilla(args.seed)

    # Modo no interactivo
    if args.demo or args.modulo is not None or args.benchmark:
        print(BANNER)
        asegurar_datos()

        if args.benchmark:
            ejecutar_benchmarks()
        elif args.demo:
            ejecutar_modulo2(datos=args.datos, interactivo=False)
            ejecutar_modulo3(datos=args.datos, interactivo=False)
            ejecutar_modulo4(datos=args.datos, interactivo=False)
        elif args.modulo == 2:
            ejecutar_modulo2(datos=args.datos, interactivo=False)
        elif args.modulo == 3:
            ejecutar_modulo3(datos=args.datos, interactivo=False)
        elif args.modulo == 4:
            ejecutar_modulo4(datos=args.datos, interactivo=False)

        print(f"\n  Reportes generados en: {REPORTS_DIR}/")
    else:
        # Modo interactivo
        menu_principal()


if __name__ == "__main__":
    main()
