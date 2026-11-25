"""
Módulo 2: Detección de comunidades de cuentas para prevención de fraude y lavado de activos.
Orquesta preprocesamiento temporal y topológico, filtrado de nodos concentradores,
ejecución de algoritmos (Louvain, Componentes por Umbral, LPA), cálculo de puntaje explicable,
detección de cuentas frontera y generación de reportes multi-formato.
"""

from __future__ import annotations
import csv
import datetime
import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.algoritmos.comunidades import (
    AlgoritmoLouvain,
    barrido_umbrales,
    calcular_modularidad,
    componentes_por_umbral_bfs,
    componentes_por_umbral_union_find,
    propagacion_etiquetas,
)
from src.graph import Edge, Graph, Node


@dataclass
class MetricasComunidad:
    """Métricas y puntaje de prioridad explicable de una comunidad detectada."""
    id_comunidad: int
    miembros: List[str]
    tamano: int
    densidad_interna: float
    flujo_interno: float
    flujo_externo: float
    ratio_flujo_interno: float
    proporcion_sospechosas: float
    volumen_total: float
    cuentas_frontera: List[str]
    puntaje_prioridad: float
    desglose_puntaje: Dict[str, float]
    transferencias_clave: List[Dict[str, Any]] = field(default_factory=list)


class AnalizadorTransaccionesFinancieras:
    """
    Motor analítico para la investigación de redes transaccionales y detección de clusters.
    """

    def __init__(
        self,
        criterio_peso: str = "combinado",
        ventana_dias: Optional[int] = 30,
        percentil_concentrador: float = 99.0,
        pesos_puntaje: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Args:
            criterio_peso: 'combinado' (n * ln(1+monto)), 'monto' o 'transferencias'.
            ventana_dias: Ventana temporal en días respecto al evento más reciente.
            percentil_concentrador: Umbral percentil para clasificar un nodo como concentrador.
            pesos_puntaje: Ponderaciones para el cálculo del score de riesgo explicable.
        """
        self.criterio_peso = criterio_peso
        self.ventana_dias = ventana_dias
        self.percentil_concentrador = percentil_concentrador
        self.pesos_puntaje = pesos_puntaje or {
            "densidad": 0.30,
            "ratio_interno": 0.30,
            "sospechosas_previas": 0.25,
            "volumen_log": 0.15,
        }
        self.nodos_excluidos: List[Dict[str, Any]] = []

    def obtener_funcion_peso(self) -> Callable[[Edge], float]:
        """Retorna la función de evaluación de peso según la estrategia configurada."""
        if self.criterio_peso == "monto":
            return lambda e: float(e.monto)
        elif self.criterio_peso == "transferencias":
            return lambda e: float(e.n_transferencias)
        else:
            # Estrategia combinada: n_transferencias * ln(1 + monto)
            return lambda e: float(e.n_transferencias) * math.log(1.0 + max(0.0, float(e.monto)))

    def preprocesar_red(
        self,
        grafo_origen: Graph,
        accion_concentrador: str = "limitar",
        limite_concentradores_exp: Optional[List[str]] = None,
    ) -> Graph:
        """
        Ejecuta el pipeline de preprocesamiento:
        1. Filtro temporal de ventana de días.
        2. Detección de concentradores legítimos (percentil o lista explícita).
        3. Proyección a grafo no dirigido agregado.
        4. Aplicación de neutralización (exclusión o tope).

        Complejidad: O(V + E) tiempo y espacio.
        """
        self.nodos_excluidos.clear()
        peso_fn = self.obtener_funcion_peso()

        # 1. Filtro temporal si existen timestamps
        aristas_filtradas = []
        fechas_validas = []

        for e in grafo_origen.iter_aristas():
            if e.timestamp:
                try:
                    dt = datetime.datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
                    fechas_validas.append(dt)
                except ValueError:
                    pass

        fecha_maxima = max(fechas_validas) if fechas_validas else None
        fecha_corte = (
            fecha_maxima - datetime.timedelta(days=self.ventana_dias)
            if (fecha_maxima and self.ventana_dias)
            else None
        )

        for e in grafo_origen.iter_aristas():
            if fecha_corte and e.timestamp:
                try:
                    dt = datetime.datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
                    if dt < fecha_corte:
                        continue
                except ValueError:
                    pass
            aristas_filtradas.append(e)

        # Construir grafo temporal intermedio
        g_temp = Graph(dirigido=grafo_origen.dirigido, ponderado=grafo_origen.ponderado)
        for n in grafo_origen.nodes.values():
            g_temp.agregar_nodo(Node(n.id, n.tipo, dict(n.atributos)))
        for e in aristas_filtradas:
            g_temp.agregar_arista(e)

        # 2. Detección de nodos concentradores por grado
        grados = [g_temp.grado(n) for n in g_temp.nodes]
        umbral_grado = float("inf")
        if grados and self.percentil_concentrador < 100.0:
            grados_ordenados = sorted(grados)
            idx = int(len(grados_ordenados) * (self.percentil_concentrador / 100.0))
            idx = min(idx, len(grados_ordenados) - 1)
            # Solo si el grado es significativo (mayor a 4)
            umbral_grado = max(5, grados_ordenados[idx])

        concentradores = set(limite_concentradores_exp or [])
        for nid in g_temp.nodes:
            if g_temp.grado(nid) >= umbral_grado:
                concentradores.add(nid)

        for cid in concentradores:
            if g_temp.existe_nodo(cid):
                self.nodos_excluidos.append({
                    "nodo": cid,
                    "grado": g_temp.grado(cid),
                    "tipo": g_temp.nodes[cid].tipo,
                    "razon": f"Concentrador con grado >= {umbral_grado} (percentil {self.percentil_concentrador}%)",
                })

        # 3. Proyectar a no dirigido
        g_no_dir = g_temp.a_no_dirigido(agregar=sum)

        # 4. Manejo de concentradores
        if accion_concentrador == "excluir":
            for c_info in self.nodos_excluidos:
                cid = c_info["nodo"]
                if g_no_dir.existe_nodo(cid):
                    g_no_dir.eliminar_nodo(cid)
        elif accion_concentrador == "limitar":
            # Limitar el peso de las aristas conectadas a un concentrador
            for c_info in self.nodos_excluidos:
                cid = c_info["nodo"]
                for v in list(g_no_dir.vecinos(cid)):
                    aristas = g_no_dir.obtener_aristas(cid, v)
                    for e in aristas:
                        e.monto = min(e.monto, 5000.0)
                        e.n_transferencias = min(e.n_transferencias, 3)

        return g_no_dir

    def detectar_comunidades_louvain(
        self,
        grafo: Graph,
        n_corridas: int = 5,
        semilla: int = 42,
    ) -> Dict[str, Any]:
        """Ejecuta el algoritmo Louvain con evaluación de estabilidad multi-semilla."""
        peso_fn = self.obtener_funcion_peso()
        louvain = AlgoritmoLouvain(gamma=1.0)
        return louvain.ejecutar_multi_semilla(
            grafo, n_corridas=n_corridas, semilla_base=semilla, peso_fn=peso_fn
        )

    def detectar_lineas_base(
        self,
        grafo: Graph,
        umbral_peso: float = 3.0,
        semilla: int = 42,
    ) -> Dict[str, Any]:
        """Ejecuta las dos líneas base: Componentes por Umbral (UF) y LPA."""
        peso_fn = self.obtener_funcion_peso()
        part_uf, _ = componentes_por_umbral_union_find(grafo, umbral_peso, peso_fn=peso_fn)
        mod_uf = calcular_modularidad(grafo, part_uf, peso_fn=peso_fn)

        part_lpa = propagacion_etiquetas(grafo, peso_fn=peso_fn, seed=semilla)
        mod_lpa = calcular_modularidad(grafo, part_lpa, peso_fn=peso_fn)

        return {
            "umbral": {
                "particion": part_uf,
                "modularidad": mod_uf,
                "umbral_usado": umbral_peso,
            },
            "lpa": {
                "particion": part_lpa,
                "modularidad": mod_lpa,
            },
        }

    def analizar_comunidades(
        self,
        grafo: Graph,
        particion: Dict[str, int],
    ) -> List[MetricasComunidad]:
        """
        Calcula las métricas operativas, cuentas frontera y puntajes de prioridad por comunidad.
        """
        peso_fn = self.obtener_funcion_peso()
        grupos: Dict[int, List[str]] = defaultdict(list)
        for nodo, cid in particion.items():
            grupos[cid].append(nodo)

        # Matriz de pesos entre comunidades y adyacencia de nodos
        peso_por_nodo_a_comunidades: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        peso_interno: Dict[int, float] = defaultdict(float)
        peso_externo: Dict[int, float] = defaultdict(float)
        volumen_total_comunidad: Dict[int, float] = defaultdict(float)
        aristas_internas_conteo: Dict[int, int] = defaultdict(int)
        transferencias_por_comunidad: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

        for e in grafo.iter_aristas():
            u, v = e.origen, e.destino
            if u not in particion or v not in particion:
                continue
            w = peso_fn(e)
            c_u, c_v = particion[u], particion[v]

            peso_por_nodo_a_comunidades[u][c_v] += w
            if u != v:
                peso_por_nodo_a_comunidades[v][c_u] += w

            if c_u == c_v:
                peso_interno[c_u] += w
                aristas_internas_conteo[c_u] += 1
                volumen_total_comunidad[c_u] += e.monto
                transferencias_por_comunidad[c_u].append({
                    "origen": u,
                    "destino": v,
                    "monto": e.monto,
                    "n_transf": e.n_transferencias,
                })
            else:
                peso_externo[c_u] += w
                peso_externo[c_v] += w
                volumen_total_comunidad[c_u] += e.monto / 2.0
                volumen_total_comunidad[c_v] += e.monto / 2.0

        metricas_lista: List[MetricasComunidad] = []

        for cid, miembros in grupos.items():
            k = len(miembros)
            # Densidad interna
            aristas_posibles = (k * (k - 1)) / 2 if k > 1 else 1
            densidad = aristas_internas_conteo[cid] / aristas_posibles if k > 1 else 0.0

            flujo_in = peso_interno[cid]
            flujo_out = peso_externo[cid]
            ratio_interno = flujo_in / (flujo_in + flujo_out + 1e-6)

            # Cuentas sospechosas marcadas previamente
            sospechosas = sum(
                1 for m in miembros
                if grafo.nodes[m].atributos.get("sospechoso", False)
            )
            prop_sospechosa = sospechosas / k if k > 0 else 0.0

            # Cuentas de frontera (vínculos relevantes a otras comunidades)
            fronteras = []
            for m in miembros:
                pesos_vecinos = peso_por_nodo_a_comunidades[m]
                peso_propia = pesos_vecinos.get(cid, 0.0)
                for otra_c, peso_otra in pesos_vecinos.items():
                    if otra_c != cid and peso_otra > 0:
                        # Si tiene interacción externa significativa (≥ 30% de la interna)
                        if peso_otra >= 0.3 * peso_propia:
                            fronteras.append(m)
                            break

            vol_total = volumen_total_comunidad[cid]
            vol_score = min(1.0, math.log1p(vol_total) / 15.0)  # Escala logarítmica normalizada

            # Score ponderado explicable [0, 100]
            desglose = {
                "densidad": self.pesos_puntaje["densidad"] * densidad,
                "ratio_interno": self.pesos_puntaje["ratio_interno"] * ratio_interno,
                "sospechosas_previas": self.pesos_puntaje["sospechosas_previas"] * prop_sospechosa,
                "volumen_log": self.pesos_puntaje["volumen_log"] * vol_score,
            }
            score_total = sum(desglose.values()) * 100.0

            # Ordenar transferencias por monto
            top_transferencias = sorted(
                transferencias_por_comunidad[cid], key=lambda x: x["monto"], reverse=True
            )[:5]

            metricas_lista.append(
                MetricasComunidad(
                    id_comunidad=cid,
                    miembros=sorted(miembros),
                    tamano=k,
                    densidad_interna=densidad,
                    flujo_interno=flujo_in,
                    flujo_externo=flujo_out,
                    ratio_flujo_interno=ratio_interno,
                    proporcion_sospechosas=prop_sospechosa,
                    volumen_total=vol_total,
                    cuentas_frontera=sorted(list(set(fronteras))),
                    puntaje_prioridad=score_total,
                    desglose_puntaje={k: round(v * 100.0, 2) for k, v in desglose.items()},
                    transferencias_clave=top_transferencias,
                )
            )

        # Ordenar comunidades por puntaje descendente
        metricas_lista.sort(key=lambda x: x.puntaje_prioridad, reverse=True)
        return metricas_lista

    def generar_reporte_markdown(
        self,
        metricas: List[MetricasComunidad],
        modularidad: float,
        estabilidad: float,
        ruta_salida: Optional[str] = None,
    ) -> str:
        """Genera un informe analítico detallado en Markdown."""
        lineas = [
            "# Reporte de Detección de Comunidades Financieras (Prevención de Fraude)",
            "",
            "## 1. Resumen Ejecutivo del Algoritmo Louvain",
            f"- **Modularidad Global Q:** `{modularidad:.4f}`",
            f"- **Estabilidad Multi-Semilla:** `{estabilidad * 100:.2f}%` de consistencia de pares",
            f"- **Comunidades Detectadas:** `{len(metricas)}`",
            f"- **Nodos Concentradores Identificados:** `{len(self.nodos_excluidos)}`",
            "",
        ]

        if self.nodos_excluidos:
            lineas.append("### Nodos Concentradores Tratados")
            lineas.append("| Nodo ID | Grado | Tipo | Acción Aplicada |")
            lineas.append("|---|---|---|---|")
            for exc in self.nodos_excluidos:
                lineas.append(f"| {exc['nodo']} | {exc['grado']} | {exc['tipo']} | {exc['razon']} |")
            lineas.append("")

        lineas.append("## 2. Clasificación de Comunidades por Nivel de Prioridad de Auditoría")
        lineas.append(
            "| ID | Cuentas | Densidad | Flujo Int / Ext | Vol. Total ($) | Score Prioridad | Cuentas Frontera |"
        )
        lineas.append("|---|---|---|---|---|---|---|")

        for m in metricas:
            lineas.append(
                f"| C-{m.id_comunidad} | {m.tamano} | {m.densidad_interna:.2f} | "
                f"{m.flujo_interno:.1f} / {m.flujo_externo:.1f} | ${m.volumen_total:,.2f} | "
                f"**{m.puntaje_prioridad:.2f}** | {', '.join(m.cuentas_frontera) or 'Ninguna'} |"
            )
        lineas.append("")

        lineas.append("## 3. Desglose Explicable de Comunidades Prioritarias")
        for m in metricas[:5]:  # Top 5 prioritarias
            lineas.append(f"### Comunidad C-{m.id_comunidad} (Score: {m.puntaje_prioridad:.2f}/100)")
            lineas.append(f"- **Miembros:** `{', '.join(m.miembros)}`")
            lineas.append(f"- **Desglose de Factores:**")
            for factor, pts in m.desglose_puntaje.items():
                lineas.append(f"  - {factor}: `{pts:.2f} pts`")
            if m.cuentas_frontera:
                lineas.append(f"- **Cuentas de Frontera (Inciertas):** `{', '.join(m.cuentas_frontera)}`")
            if m.transferencias_clave:
                lineas.append("- **Transferencias Principales:**")
                for t in m.transferencias_clave:
                    lineas.append(
                        f"  - {t['origen']} ➔ {t['destino']}: ${t['monto']:,.2f} ({t['n_transf']} transacciones)"
                    )
            lineas.append("")

        resultado_md = "\n".join(lineas)
        if ruta_salida:
            os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(resultado_md)

        return resultado_md
