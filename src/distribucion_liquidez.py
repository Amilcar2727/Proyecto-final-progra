"""
Módulo 4: Planificación y Optimización de la Distribución de Liquidez hacia Bóvedas y Agencias.
Modela el suministro de efectivo como un problema de flujo en redes con super-fuente y super-sumidero,
resuelve el flujo máximo con Dinic (y compara con Edmonds-Karp y Ford-Fulkerson),
extrae el corte mínimo, distingue saturación de cuello de botella real,
y ejecuta un análisis de sensibilidad marginal (+δ) para priorizar inversiones operativas.
"""

from __future__ import annotations
import csv
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from src.algoritmos.flujo import (
    ResultadoFlujo,
    construir_red_residual_desde_grafo,
    dinic_flujo_maximo,
    edmonds_karp_flujo_maximo,
    ford_fulkerson_dfs,
)
from src.graph import Edge, Graph, Node

ID_SUPER_FUENTE = "_SUPER_FUENTE_S_"
ID_SUPER_SUMIDERO = "_SUPER_SUMIDERO_T_"


@dataclass
class ImpactoCuelloBotella:
    """Evaluación de impacto marginal por aumento de capacidad en una ruta crítica."""
    origen: str
    destino: str
    capacidad_actual: float
    flujo_actual: float
    incremento_evaluado: float
    nuevo_flujo_global: float
    ganancia_marginal: float
    eficiencia_inversion: float


class PlanificadorDistribucionLiquidez:
    """
    Controlador logístico para la planificación y optimización del transporte de efectivo.
    """

    def __init__(self, delta_sensibilidad: float = 50000.0) -> None:
        self.delta_sensibilidad = delta_sensibilidad

    def preparar_red_con_supernodos(
        self,
        grafo_base: Graph,
        disponibilidad_bovedas: Dict[str, float],
        demanda_agencias: Dict[str, float],
    ) -> Graph:
        """
        Construye una red aumentada agregando una super-fuente conectada a las bóvedas
        y un super-sumidero conectado desde agencias/ATM.
        """
        g_red = Graph(dirigido=True, ponderado=True)

        # Copiar nodos base
        for n in grafo_base.nodes.values():
            g_red.agregar_nodo(Node(n.id, n.tipo, dict(n.atributos)))

        # Agregar super-nodos
        g_red.agregar_nodo(Node(ID_SUPER_FUENTE, "boveda_central"))
        g_red.agregar_nodo(Node(ID_SUPER_SUMIDERO, "entidad"))

        # Copiar aristas físicas existentes
        for e in grafo_base.iter_aristas():
            if e.disponible and e.capacidad > 0:
                g_red.agregar_arista(
                    Edge(
                        origen=e.origen,
                        destino=e.destino,
                        capacidad=e.capacidad,
                        costo_unitario=e.costo_unitario,
                        disponible=e.disponible,
                        canal=e.canal,
                    )
                )

        # Conectar Super-Fuente S -> Bóvedas
        for boveda_id, oferta in disponibilidad_bovedas.items():
            if oferta > 0:
                if not g_red.existe_nodo(boveda_id):
                    g_red.agregar_nodo(Node(boveda_id, "boveda_central"))
                g_red.agregar_arista(
                    Edge(
                        origen=ID_SUPER_FUENTE,
                        destino=boveda_id,
                        capacidad=oferta,
                        disponible=True,
                        canal="super_fuente",
                    )
                )

        # Conectar Agencias/ATM -> Super-Sumidero T
        for agencia_id, demanda in demanda_agencias.items():
            if demanda > 0:
                if not g_red.existe_nodo(agencia_id):
                    g_red.agregar_nodo(Node(agencia_id, "agencia"))
                g_red.agregar_arista(
                    Edge(
                        origen=agencia_id,
                        destino=ID_SUPER_SUMIDERO,
                        capacidad=demanda,
                        disponible=True,
                        canal="super_sumidero",
                    )
                )

        return g_red

    def optimizar_flujo_dinic(
        self,
        grafo_base: Graph,
        disponibilidad_bovedas: Dict[str, float],
        demanda_agencias: Dict[str, float],
    ) -> ResultadoFlujo:
        """Calcula el flujo máximo óptimo mediante el algoritmo Dinic."""
        g_aumentado = self.preparar_red_con_supernodos(
            grafo_base, disponibilidad_bovedas, demanda_agencias
        )
        red_residual = construir_red_residual_desde_grafo(
            g_aumentado, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO
        )
        return dinic_flujo_maximo(red_residual, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO)

    def optimizar_flujo_edmonds_karp(
        self,
        grafo_base: Graph,
        disponibilidad_bovedas: Dict[str, float],
        demanda_agencias: Dict[str, float],
    ) -> ResultadoFlujo:
        """Calcula el flujo máximo mediante Edmonds-Karp para fines comparativos."""
        g_aumentado = self.preparar_red_con_supernodos(
            grafo_base, disponibilidad_bovedas, demanda_agencias
        )
        red_residual = construir_red_residual_desde_grafo(
            g_aumentado, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO
        )
        return edmonds_karp_flujo_maximo(red_residual, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO)

    def optimizar_flujo_ford_fulkerson(
        self,
        grafo_base: Graph,
        disponibilidad_bovedas: Dict[str, float],
        demanda_agencias: Dict[str, float],
    ) -> ResultadoFlujo:
        """Calcula el flujo máximo mediante Ford-Fulkerson clásico para fines comparativos."""
        g_aumentado = self.preparar_red_con_supernodos(
            grafo_base, disponibilidad_bovedas, demanda_agencias
        )
        red_residual = construir_red_residual_desde_grafo(
            g_aumentado, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO
        )
        return ford_fulkerson_dfs(red_residual, ID_SUPER_FUENTE, ID_SUPER_SUMIDERO)

    def analizar_sensibilidad_cuellos_botella(
        self,
        grafo_base: Graph,
        disponibilidad_bovedas: Dict[str, float],
        demanda_agencias: Dict[str, float],
        resultado_base: Optional[ResultadoFlujo] = None,
    ) -> List[ImpactoCuelloBotella]:
        """
        Para cada cuello de botella perteneciente al corte mínimo, evalúa el incremento
        marginal en efectivo distribuido al elevar la capacidad en δ unidades.
        """
        if resultado_base is None:
            resultado_base = self.optimizar_flujo_dinic(
                grafo_base, disponibilidad_bovedas, demanda_agencias
            )

        flujo_base = resultado_base.flujo_maximo
        analisis_impacto: List[ImpactoCuelloBotella] = []

        # Filtrar solo cuellos de botella que corresponden a rutas físicas (no a super-nodos)
        rutas_criticas = [
            (u, v) for u, v in resultado_base.cuellos_de_botella
            if u != ID_SUPER_FUENTE and v != ID_SUPER_SUMIDERO
        ]

        for u, v in rutas_criticas:
            # Crear copia del grafo base y aumentar capacidad de u->v
            g_mod = grafo_base.copiar()
            aristas_uv = g_mod.obtener_aristas(u, v)
            cap_actual = aristas_uv[0].capacidad if aristas_uv else 0.0

            for e in aristas_uv:
                e.capacidad += self.delta_sensibilidad

            res_nuevo = self.optimizar_flujo_dinic(
                g_mod, disponibilidad_bovedas, demanda_agencias
            )
            ganancia = max(0.0, res_nuevo.flujo_maximo - flujo_base)
            flujo_actual_arista = resultado_base.flujo_aristas.get((u, v), 0.0)

            analisis_impacto.append(
                ImpactoCuelloBotella(
                    origen=u,
                    destino=v,
                    capacidad_actual=cap_actual,
                    flujo_actual=flujo_actual_arista,
                    incremento_evaluado=self.delta_sensibilidad,
                    nuevo_flujo_global=res_nuevo.flujo_maximo,
                    ganancia_marginal=ganancia,
                    eficiencia_inversion=(ganancia / self.delta_sensibilidad) if self.delta_sensibilidad > 0 else 0.0,
                )
            )

        # Ordenar por ganancia marginal descendente
        analisis_impacto.sort(key=lambda x: x.ganancia_marginal, reverse=True)
        return analisis_impacto

    def generar_reporte_distribucion(
        self,
        grafo_base: Graph,
        disponibilidad_bovedas: Dict[str, float],
        demanda_agencias: Dict[str, float],
        resultado: ResultadoFlujo,
        sensibilidad: List[ImpactoCuelloBotella],
        ruta_salida: Optional[str] = None,
    ) -> str:
        """Genera un reporte técnico de distribución de liquidez en Markdown."""
        oferta_total = sum(disponibilidad_bovedas.values())
        demanda_total = sum(demanda_agencias.values())
        efectivo_entregado = resultado.flujo_maximo
        deficit_global = max(0.0, demanda_total - efectivo_entregado)

        # Distinción de saturadas vs cuellos de botella
        corte_set = set(resultado.cuellos_de_botella)
        saturadas_no_criticas = [
            (u, v) for u, v in resultado.aristas_saturadas
            if (u, v) not in corte_set and u != ID_SUPER_FUENTE and v != ID_SUPER_SUMIDERO
        ]
        cuellos_fisicos = [
            (u, v) for u, v in resultado.cuellos_de_botella
            if u != ID_SUPER_FUENTE and v != ID_SUPER_SUMIDERO
        ]

        lineas = [
            "# Reporte de Planificación y Distribución de Liquidez hacia Bóvedas",
            "",
            "## 1. Balance Financiero Global de Liquidez",
            f"- **Disponibilidad Total en Bóvedas:** `${oferta_total:,.2f}`",
            f"- **Demanda Total de Agencias/ATM:** `${demanda_total:,.2f}`",
            f"- **Efectivo Efectivamente Distribuido:** `${efectivo_entregado:,.2f}`",
            f"- **Déficit Insatisfecho:** `${deficit_global:,.2f}`",
            f"- **Capacidad Teórica del Corte Mínimo:** `${resultado.capacidad_corte:,.2f}`",
            f"- **Teorema Max-Flow / Min-Cut Verificado:** `{'SÍ (Flujo == Capacidad Corte)' if abs(resultado.flujo_maximo - resultado.capacidad_corte) < 1e-4 else 'DISCREPANCIA'}`",
            f"- **Conservación de Flujo en Nodos Intermedios:** `{'VÁLIDA' if resultado.conservacion_valida else 'FALLA'}`",
            f"- **Respeto Estricto de Capacidades:** `{'VÁLIDO' if resultado.capacidades_respetadas else 'EXCEDIDO'}`",
            "",
            "## 2. Nivel de Abastecimiento por Agencia / ATM",
            "| Agencia / ATM | Demanda Requerida ($) | Efectivo Recibido ($) | Déficit ($) | Cumplimiento (%) |",
            "|---|---|---|---|---|",
        ]

        for ag_id, req in sorted(demanda_agencias.items()):
            recibido = resultado.flujo_aristas.get((ag_id, ID_SUPER_SUMIDERO), 0.0)
            defic = max(0.0, req - recibido)
            cumplimiento = (recibido / req * 100.0) if req > 0 else 100.0
            lineas.append(
                f"| {ag_id} | ${req:,.2f} | ${recibido:,.2f} | ${defic:,.2f} | {cumplimiento:.1f}% |"
            )
        lineas.append("")

        lineas.append("## 3. Despacho desde Bóvedas Centrales y Regionales")
        lineas.append("| Bóveda | Oferta Inicial ($) | Efectivo Despachado ($) | Remanente en Bóveda ($) | % Utilizado |")
        lineas.append("|---|---|---|---|---|")
        for bv_id, disp in sorted(disponibilidad_bovedas.items()):
            despachado = resultado.flujo_aristas.get((ID_SUPER_FUENTE, bv_id), 0.0)
            remanente = max(0.0, disp - despachado)
            utilizado = (despachado / disp * 100.0) if disp > 0 else 0.0
            lineas.append(
                f"| {bv_id} | ${disp:,.2f} | ${despachado:,.2f} | ${remanente:,.2f} | {utilizado:.1f}% |"
            )
        lineas.append("")

        lineas.append("## 4. Cuellos de Botella Reales (Corte Mínimo) vs Rutas Saturadas No Críticas")
        lineas.append(
            "> **Distinción Teórica Fundamental:** Una ruta puede alcanzar el 100% de su capacidad "
            "(estar saturada) sin ser cuello de botella del sistema si existen caminos alternativos redundantes "
            "con holgura. Por el contrario, las aristas del **Corte Mínimo** son las que limitan matemáticamente "
            "el flujo total global; ampliar cualquier otra ruta no aporta nada a la distribución global."
        )
        lineas.append("")
        lineas.append("### Cuellos de Botella Reales (Pertenecen al Corte Mínimo)")
        if cuellos_fisicos:
            for u, v in cuellos_fisicos:
                cap = grafo_base.obtener_aristas(u, v)[0].capacidad if grafo_base.obtener_aristas(u, v) else 0.0
                lineas.append(f"- **{u} ➔ {v}**: Capacidad saturada `${cap:,.2f}` (Limita el flujo de la red)")
        else:
            lineas.append("- Ninguna ruta física limita el sistema (la restricción está en oferta o demanda de origen/destino).")
        lineas.append("")

        if saturadas_no_criticas:
            lineas.append("### Rutas Saturadas No Críticas (Fuera del Corte Mínimo)")
            for u, v in saturadas_no_criticas:
                cap = grafo_base.obtener_aristas(u, v)[0].capacidad if grafo_base.obtener_aristas(u, v) else 0.0
                lineas.append(f"- {u} ➔ {v}: Capacidad `${cap:,.2f}` saturada, pero no frena el flujo global.")
            lineas.append("")

        lineas.append("## 5. Análisis de Sensibilidad y Priorización de Inversión Logística")
        lineas.append(
            f"Evaluación del impacto al aumentar la capacidad en **+${self.delta_sensibilidad:,.2f}** en cada cuello de botella:"
        )
        lineas.append("")
        lineas.append(
            "| Prioridad | Ruta Cuello de Botella | Capacidad Actual ($) | Flujo Actual ($) | Ganancia Marginal ($) | Retorno Marginal de Inversión |"
        )
        lineas.append("|---|---|---|---|---|---|")

        for idx, s in enumerate(sensibilidad, start=1):
            lineas.append(
                f"| **P-{idx}** | {s.origen} ➔ {s.destino} | ${s.capacidad_actual:,.2f} | "
                f"${s.flujo_actual:,.2f} | **+${s.ganancia_marginal:,.2f}** | {s.eficiencia_inversion * 100:.1f}% |"
            )
        lineas.append("")

        md_str = "\n".join(lineas)
        if ruta_salida:
            os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(md_str)

        return md_str
