"""
Módulo 3: Enrutamiento Financiero y Diseño de Red Troncal de Menor Costo (MST).
Orquesta la selección óptima de enlaces de comunicación entre agencias, ATM y sedes,
evaluando costos de instalación y operativos, latencia, fragilidad (puentes y articulaciones),
escenarios 'what-if' (enlaces obligatorios y prohibidos), rutas alternativas y ahorro económico.
"""

from __future__ import annotations
import csv
import json
import os
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.algoritmos.arbol_expansion import (
    ResultadoMST,
    kruskal_mst,
    prim_mst,
)
from src.algoritmos.recorridos import (
    bfs_camino_mas_corto,
    encontrar_puentes_y_articulaciones,
)
from src.graph import Edge, Graph, Node


class OptimizadorRedTroncal:
    """
    Controlador para el diseño óptimo de redes troncales financieras y análisis de enrutamiento.
    """

    def __init__(
        self,
        horizonte_meses: float = 12.0,
        alpha_costo: float = 1.0,
        beta_latencia: float = 0.0,
    ) -> None:
        """
        Args:
            horizonte_meses: Horizonte temporal para amortizar costos operativos mensuales.
            alpha_costo: Factor de ponderación para la dimensión económica.
            beta_latencia: Factor de ponderación para penalización por latencia/tiempo.
        """
        self.horizonte_meses = horizonte_meses
        self.alpha_costo = alpha_costo
        self.beta_latencia = beta_latencia

    def funcion_costo(self, arista: Edge) -> float:
        """
        Calcula el costo ponderado del enlace combinando Capex, Opex y latencia:
        w = alpha * (instalacion + operativo * horizonte) + beta * latencia
        """
        costo_financiero = arista.costo_instalacion + (arista.costo_operativo * self.horizonte_meses)
        return (self.alpha_costo * costo_financiero) + (self.beta_latencia * arista.tiempo)

    def ejecutar_kruskal(
        self,
        grafo: Graph,
        obligatorias: Optional[Set[Tuple[str, str]]] = None,
        prohibidas: Optional[Set[Tuple[str, str]]] = None,
    ) -> ResultadoMST:
        """Diseña la red troncal de costo mínimo usando Kruskal con Union-Find."""
        return kruskal_mst(
            grafo,
            peso_fn=self.funcion_costo,
            aristas_obligatorias=obligatorias,
            aristas_prohibidas=prohibidas,
        )

    def ejecutar_prim(self, grafo: Graph, nodo_inicio: Optional[str] = None) -> ResultadoMST:
        """Diseña la red troncal usando Prim con min-heap binario."""
        return prim_mst(
            grafo,
            peso_fn=self.funcion_costo,
            nodo_inicio=nodo_inicio,
        )

    def construir_grafo_mst(self, grafo_base: Graph, resultado: ResultadoMST) -> Graph:
        """Genera una instancia de Graph conteniendo únicamente las aristas seleccionadas en el MST."""
        g_mst = Graph(dirigido=False, ponderado=True)
        for n in grafo_base.nodes.values():
            g_mst.agregar_nodo(Node(n.id, n.tipo, dict(n.atributos)))
        for e in resultado.aristas_mst:
            g_mst.agregar_arista(e)
        return g_mst

    def analizar_fragilidad(
        self,
        grafo_completo: Graph,
        resultado_mst: ResultadoMST,
        top_k_redundancia: int = 5,
    ) -> Dict[str, Any]:
        """
        Evalúa la vulnerabilidad de la red troncal determinando puentes, puntos de articulación
        y proponiendo los enlaces de menor costo para redundancia operativa.
        """
        g_mst = self.construir_grafo_mst(grafo_completo, resultado_mst)
        puentes, articulaciones = encontrar_puentes_y_articulaciones(g_mst)

        # En un árbol, toda arista no terminal es un puente crítico
        aristas_mst_set = {
            (min(e.origen, e.destino), max(e.origen, e.destino))
            for e in resultado_mst.aristas_mst
        }

        # Identificar enlaces candidatos en el grafo original no seleccionados
        candidatas_redundancia = []
        for e in grafo_completo.iter_aristas():
            if not e.disponible:
                continue
            par = (min(e.origen, e.destino), max(e.origen, e.destino))
            if par not in aristas_mst_set:
                costo = self.funcion_costo(e)
                # Beneficio: si conecta con algún punto de articulación
                involucra_critico = (e.origen in articulaciones or e.destino in articulaciones)
                candidatas_redundancia.append({
                    "origen": e.origen,
                    "destino": e.destino,
                    "costo": costo,
                    "latencia": e.tiempo,
                    "involucra_critico": involucra_critico,
                    "edge": e,
                })

        # Ordenar primero las que dan redundancia a puntos críticos y luego por menor costo
        candidatas_redundancia.sort(key=lambda x: (not x["involucra_critico"], x["costo"]))
        sugerencias = candidatas_redundancia[:top_k_redundancia]

        return {
            "puentes_criticos": puentes,
            "puntos_articulacion": sorted(list(articulaciones)),
            "total_puentes": len(puentes),
            "total_articulaciones": len(articulaciones),
            "sugerencias_redundancia": sugerencias,
        }

    def calcular_ahorro_economico(
        self, grafo_completo: Graph, resultado_mst: ResultadoMST
    ) -> Dict[str, float]:
        """Compara el costo de la red completa frente a la red troncal optimizada."""
        costo_red_completa = sum(
            self.funcion_costo(e)
            for e in grafo_completo.iter_aristas()
            if e.disponible
        )
        costo_mst = resultado_mst.peso_total
        ahorro_absoluto = max(0.0, costo_red_completa - costo_mst)
        porcentaje_ahorro = (
            (ahorro_absoluto / costo_red_completa * 100.0) if costo_red_completa > 0 else 0.0
        )

        return {
            "costo_red_completa": costo_red_completa,
            "costo_red_troncal": costo_mst,
            "ahorro_absoluto": ahorro_absoluto,
            "porcentaje_ahorro": porcentaje_ahorro,
        }

    def consultar_ruta_troncal(
        self,
        grafo_completo: Graph,
        resultado_mst: ResultadoMST,
        origen: str,
        destino: str,
    ) -> Dict[str, Any]:
        """
        Calcula el camino único entre origen y destino sobre el MST
        y lo contrasta contra el enlace directo o la ruta más corta en la red original.
        """
        g_mst = self.construir_grafo_mst(grafo_completo, resultado_mst)
        camino_mst = bfs_camino_mas_corto(g_mst, origen, destino)

        costo_camino_mst = 0.0
        latencia_camino_mst = 0.0

        if camino_mst and len(camino_mst) > 1:
            for i in range(len(camino_mst) - 1):
                u, v = camino_mst[i], camino_mst[i + 1]
                aristas = g_mst.obtener_aristas(u, v)
                if aristas:
                    e = aristas[0]
                    costo_camino_mst += self.funcion_costo(e)
                    latencia_camino_mst += e.tiempo

        # Enlace directo si existe en red original
        enlace_directo = None
        aristas_directas = grafo_completo.obtener_aristas(origen, destino)
        if not aristas_directas and not grafo_completo.dirigido:
            aristas_directas = grafo_completo.obtener_aristas(destino, origen)

        if aristas_directas:
            e_dir = aristas_directas[0]
            enlace_directo = {
                "existe": True,
                "costo": self.funcion_costo(e_dir),
                "latencia": e_dir.tiempo,
                "disponible": e_dir.disponible,
            }
        else:
            enlace_directo = {"existe": False}

        return {
            "origen": origen,
            "destino": destino,
            "camino_mst": camino_mst,
            "saltos_mst": len(camino_mst) - 1 if camino_mst else 0,
            "costo_mst": costo_camino_mst,
            "latencia_mst": latencia_camino_mst,
            "enlace_directo": enlace_directo,
        }

    def generar_reporte_markdown(
        self,
        resultado_kruskal: ResultadoMST,
        resultado_prim: ResultadoMST,
        fragilidad: Dict[str, Any],
        ahorro: Dict[str, float],
        ruta_salida: Optional[str] = None,
    ) -> str:
        """Genera un reporte técnico de diseño de red troncal en Markdown."""
        lineas = [
            "# Reporte de Optimización de Red Troncal Financiera (MST)",
            "",
            "## 1. Resumen de Optimización y Costos",
            f"- **Costo Red Troncal Óptima (Kruskal):** `${resultado_kruskal.peso_total:,.2f}`",
            f"- **Costo Red Troncal Óptima (Prim):** `${resultado_prim.peso_total:,.2f}`",
            f"- **Costo Red Completa Candidata:** `${ahorro['costo_red_completa']:,.2f}`",
            f"- **Ahorro Financiero Obtenido:** `${ahorro['ahorro_absoluto']:,.2f}` (`{ahorro['porcentaje_ahorro']:.2f}%`)",
            f"- **Componentes Conexas:** `{resultado_kruskal.num_componentes}`",
            f"- **Total Enlaces Seleccionados:** `{len(resultado_kruskal.aristas_mst)}`",
            "",
            "## 2. Enlaces Troncales Seleccionados (Secuencia Kruskal)",
            "| Paso | Origen | Destino | Costo Instalación ($) | Costo Operativo ($/mes) | Latencia (ms) | Costo Ponderado ($) |",
            "|---|---|---|---|---|---|---|",
        ]

        for paso, (u, v, w) in enumerate(resultado_kruskal.orden_seleccion, start=1):
            e = next(
                edge for edge in resultado_kruskal.aristas_mst
                if (edge.origen == u and edge.destino == v) or (edge.origen == v and edge.destino == u)
            )
            lineas.append(
                f"| {paso} | {u} | {v} | ${e.costo_instalacion:,.2f} | ${e.costo_operativo:,.2f} | {e.tiempo:.1f} ms | ${w:,.2f} |"
            )
        lineas.append("")

        if resultado_kruskal.num_componentes > 1:
            lineas.append("### Alerta: Red Desconectada (Bosque de Expansión)")
            lineas.append(f"Se identificaron {resultado_kruskal.num_componentes} componentes aisladas sin enlace candidato viable.")
            for cid, nodos_comp in enumerate(resultado_kruskal.componentes, start=1):
                lineas.append(f"- **Componente {cid}:** `{', '.join(sorted(list(nodos_comp)))}`")
            lineas.append("")

        lineas.append("## 3. Análisis de Fragilidad y Vulnerabilidad de la Red Troncal")
        lineas.append(f"- **Total Puntos de Articulación (Nodos Críticos):** `{fragilidad['total_articulaciones']}`")
        lineas.append(f"- **Total Puentes Críticos (Enlaces Cuello de Botella):** `{fragilidad['total_puentes']}`")
        lineas.append(f"- **Puntos de Articulación:** `{', '.join(fragilidad['puntos_articulacion']) or 'Ninguno'}`")
        lineas.append("")

        if fragilidad["sugerencias_redundancia"]:
            lineas.append("### Enlaces de Redundancia Recomendados (Menor Costo)")
            lineas.append("| Origen | Destino | Costo Proyectado ($) | Latencia (ms) | Protege Punto Crítico |")
            lineas.append("|---|---|---|---|---|")
            for sug in fragilidad["sugerencias_redundancia"]:
                lineas.append(
                    f"| {sug['origen']} | {sug['destino']} | ${sug['costo']:,.2f} | {sug['latencia']:.1f} ms | "
                    f"{'Sí' if sug['involucra_critico'] else 'No'} |"
                )
            lineas.append("")

        md_contenido = "\n".join(lineas)
        if ruta_salida:
            os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(md_contenido)

        return md_contenido
