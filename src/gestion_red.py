"""
Módulo de gestión y modelamiento de redes financieras (Módulo 1).
Maneja la carga, validación exhaustiva, serialización y persistencia de grafos.

Justificación teórica de la estructura de datos:
- Lista de Adyacencia dict[str, dict[str, list[Edge]]]:
  - Espacio: O(V + E), óptimo para redes financieras reales que son esparsas (|E| << |V|^2).
  - Iteración sobre adyacencias: O(deg(u)), permitiendo algoritmos rápidos (Dinic, Kruskal, Louvain).
- Matriz de Adyacencia:
  - Espacio: O(V^2), prohibitivo para redes de 10,000+ cuentas bancarias (consumiría >100 millones de celdas).
  - Solo sería preferible en redes extremadamente densas (E ≈ V^2) o donde la operación dominante
    sea la consulta de existencia de arista u-v en O(1) tiempo estricto sin restricciones de memoria.
"""

from __future__ import annotations
import csv
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from src.graph import Edge, Graph, Node, TIPOS_NODO_VALIDOS


class ErrorRedFinanciera(Exception):
    """Excepción base para fallas en el modelado de redes financieras."""
    pass


class ErrorValidacionRed(ErrorRedFinanciera):
    """Excepción lanzada cuando uno o más registros violan las restricciones de negocio."""
    def __init__(self, mensaje: str, errores: Optional[List[str]] = None):
        super().__init__(mensaje)
        self.errores = errores or []


class ErrorNodoInexistente(ErrorRedFinanciera):
    """Referencia a un nodo no declarado en modo estricto."""
    pass


class ErrorValorInvalido(ErrorRedFinanciera):
    """Valor numérico o tipológico no permitido (ej. riesgo fuera de [0,1], monto < 0)."""
    pass


class ErrorArchivoInvalido(ErrorRedFinanciera):
    """Falla en lectura, formato no soportado o sintaxis de archivo."""
    pass


class GestorRedFinanciera:
    """
    Controlador para administración, validación y persistencia de redes financieras.
    """

    def __init__(self, grafo: Optional[Graph] = None) -> None:
        self.grafo: Graph = grafo if grafo is not None else Graph(dirigido=True, ponderado=True)
        self.errores_registro: List[str] = []
        self.advertencias: List[str] = []

    def limpiar_errores(self) -> None:
        self.errores_registro.clear()
        self.advertencias.clear()

    def cargar_desde_json(
        self, ruta_archivo: str, estricto: bool = True
    ) -> Graph:
        """
        Carga una red financiera desde un archivo JSON estructurado.

        Formato esperado:
        {
            "dirigido": bool,
            "ponderado": bool,
            "nodos": [{"id": "A", "tipo": "cuenta", "atributos": {...}}],
            "aristas": [{"origen": "A", "destino": "B", "monto": 100.0, ...}]
        }
        """
        self.limpiar_errores()
        if not os.path.exists(ruta_archivo):
            raise ErrorArchivoInvalido(f"El archivo '{ruta_archivo}' no existe.")

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except Exception as e:
            raise ErrorArchivoInvalido(f"Error al parsear archivo JSON: {e}") from e

        dirigido = datos.get("dirigido", True)
        ponderado = datos.get("ponderado", True)
        grafo = Graph(dirigido=dirigido, ponderado=ponderado)

        # 1. Cargar y validar nodos
        nodos_declarados: Set[str] = set()
        for idx, item in enumerate(datos.get("nodos", []), start=1):
            nodo_id = str(item.get("id", "")).strip()
            tipo = item.get("tipo", "cuenta").strip()
            atributos = item.get("atributos", {})

            if not nodo_id:
                self.errores_registro.append(f"Línea nodo {idx}: 'id' vacío o ausente.")
                continue

            if tipo not in TIPOS_NODO_VALIDOS:
                self.errores_registro.append(
                    f"Línea nodo {idx}: Tipo '{tipo}' no válido para nodo '{nodo_id}'."
                )
                if estricto:
                    continue

            if nodo_id in nodos_declarados:
                self.advertencias.append(f"Línea nodo {idx}: Nodo duplicado '{nodo_id}'. Se actualizarán atributos.")

            grafo.agregar_nodo(Node(id=nodo_id, tipo=tipo if tipo in TIPOS_NODO_VALIDOS else "cuenta", atributos=atributos))
            nodos_declarados.add(nodo_id)

        # 2. Cargar y validar aristas
        for idx, item in enumerate(datos.get("aristas", []), start=1):
            origen = str(item.get("origen", "")).strip()
            destino = str(item.get("destino", "")).strip()

            if not origen or not destino:
                self.errores_registro.append(f"Línea arista {idx}: origen o destino ausente.")
                continue

            if estricto and (origen not in nodos_declarados or destino not in nodos_declarados):
                self.errores_registro.append(
                    f"Línea arista {idx}: Conexión entre nodos no declarados ({origen} -> {destino})."
                )
                continue

            # Validar autolazos
            if origen == destino:
                self.advertencias.append(f"Línea arista {idx}: Autolazo detectado en nodo '{origen}'.")

            try:
                monto = float(item.get("monto", 0.0))
                if monto < 0:
                    self.errores_registro.append(f"Línea arista {idx}: Monto negativo ({monto}).")
                    if estricto:
                        continue
            except (ValueError, TypeError):
                self.errores_registro.append(f"Línea arista {idx}: Monto no numérico.")
                if estricto:
                    continue

            try:
                capacidad = float(item.get("capacidad", 0.0))
                if capacidad < 0:
                    self.errores_registro.append(f"Línea arista {idx}: Capacidad negativa ({capacidad}).")
                    if estricto:
                        continue
            except (ValueError, TypeError):
                self.errores_registro.append(f"Línea arista {idx}: Capacidad no numérica.")
                if estricto:
                    continue

            try:
                riesgo = float(item.get("riesgo", 0.0))
                if not (0.0 <= riesgo <= 1.0):
                    self.errores_registro.append(f"Línea arista {idx}: Riesgo fuera de [0, 1] ({riesgo}).")
                    if estricto:
                        continue
            except (ValueError, TypeError):
                self.errores_registro.append(f"Línea arista {idx}: Riesgo no numérico.")
                if estricto:
                    continue

            edge = Edge(
                origen=origen,
                destino=destino,
                monto=max(0.0, monto),
                timestamp=item.get("timestamp"),
                n_transferencias=int(item.get("n_transferencias", 1)),
                comision=float(item.get("comision", 0.0)),
                costo_instalacion=float(item.get("costo_instalacion", 0.0)),
                costo_operativo=float(item.get("costo_operativo", 0.0)),
                tiempo=float(item.get("tiempo", 0.0)),
                capacidad=max(0.0, capacidad),
                costo_unitario=float(item.get("costo_unitario", 0.0)),
                riesgo=min(max(0.0, riesgo), 1.0),
                disponible=bool(item.get("disponible", True)),
                canal=str(item.get("canal", "general")),
                atributos=item.get("atributos", {}),
            )
            grafo.agregar_arista(edge)

        if estricto and self.errores_registro:
            raise ErrorValidacionRed(
                f"Se encontraron {len(self.errores_registro)} errores en validación estricta.",
                self.errores_registro,
            )

        self.grafo = grafo
        return grafo

    def cargar_desde_csv(
        self,
        ruta_archivo: str,
        delimitador: str = ",",
        dirigido: bool = True,
        ponderado: bool = True,
        estricto: bool = True,
    ) -> Graph:
        """
        Carga una red desde archivo CSV o TXT delimitado.
        Soporta columnas estándar:
        origen, destino, monto, n_transferencias, comision, costo_instalacion,
        costo_operativo, tiempo, capacidad, costo_unitario, riesgo, disponible, canal, timestamp.
        """
        self.limpiar_errores()
        if not os.path.exists(ruta_archivo):
            raise ErrorArchivoInvalido(f"El archivo '{ruta_archivo}' no existe.")

        grafo = Graph(dirigido=dirigido, ponderado=ponderado)

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                lector = csv.DictReader(f, delimiter=delimitador)
                if not lector.fieldnames:
                    raise ErrorArchivoInvalido("El archivo CSV no contiene cabecera.")

                for num_linea, fila in enumerate(lector, start=2):
                    # Normalizar nombres de columnas a minúsculas y sin espacios
                    fila_norm = {k.strip().lower(): (v.strip() if v else "") for k, v in fila.items() if k}

                    origen = fila_norm.get("origen", "")
                    destino = fila_norm.get("destino", "")

                    if not origen or not destino:
                        self.errores_registro.append(
                            f"Línea {num_linea}: Registro sin origen o destino válido."
                        )
                        continue

                    # Validaciones numéricas
                    try:
                        monto = float(fila_norm.get("monto", 0.0) or 0.0)
                        if monto < 0:
                            self.errores_registro.append(f"Línea {num_linea}: Monto negativo ({monto}).")
                            if estricto:
                                continue
                    except ValueError:
                        self.errores_registro.append(f"Línea {num_linea}: Monto no numérico.")
                        if estricto:
                            continue

                    try:
                        capacidad = float(fila_norm.get("capacidad", 0.0) or 0.0)
                        if capacidad < 0:
                            self.errores_registro.append(f"Línea {num_linea}: Capacidad negativa.")
                            if estricto:
                                continue
                    except ValueError:
                        self.errores_registro.append(f"Línea {num_linea}: Capacidad no numérica.")
                        if estricto:
                            continue

                    try:
                        riesgo = float(fila_norm.get("riesgo", 0.0) or 0.0)
                        if not (0.0 <= riesgo <= 1.0):
                            self.errores_registro.append(f"Línea {num_linea}: Riesgo fuera de [0,1].")
                            if estricto:
                                continue
                    except ValueError:
                        self.errores_registro.append(f"Línea {num_linea}: Riesgo no numérico.")
                        if estricto:
                            continue

                    disponible_str = fila_norm.get("disponible", "true").lower()
                    disponible = disponible_str not in {"false", "0", "no", "falso"}

                    edge = Edge(
                        origen=origen,
                        destino=destino,
                        monto=max(0.0, monto),
                        timestamp=fila_norm.get("timestamp") or None,
                        n_transferencias=int(fila_norm.get("n_transferencias", 1) or 1),
                        comision=float(fila_norm.get("comision", 0.0) or 0.0),
                        costo_instalacion=float(fila_norm.get("costo_instalacion", 0.0) or 0.0),
                        costo_operativo=float(fila_norm.get("costo_operativo", 0.0) or 0.0),
                        tiempo=float(fila_norm.get("tiempo", 0.0) or 0.0),
                        capacidad=max(0.0, capacidad),
                        costo_unitario=float(fila_norm.get("costo_unitario", 0.0) or 0.0),
                        riesgo=min(max(0.0, riesgo), 1.0),
                        disponible=disponible,
                        canal=fila_norm.get("canal", "general") or "general",
                    )
                    grafo.agregar_arista(edge)

        except Exception as e:
            if not isinstance(e, ErrorRedFinanciera):
                raise ErrorArchivoInvalido(f"Error procesando CSV: {e}") from e
            raise

        if estricto and self.errores_registro:
            raise ErrorValidacionRed(
                f"Se detectaron {len(self.errores_registro)} inconsistencias en validación estricta.",
                self.errores_registro,
            )

        self.grafo = grafo
        return grafo

    def exportar_a_json(self, ruta_archivo: str) -> None:
        """Exporta el grafo actual a un archivo JSON reproducible."""
        os.makedirs(os.path.dirname(os.path.abspath(ruta_archivo)), exist_ok=True)
        datos = {
            "dirigido": self.grafo.dirigido,
            "ponderado": self.grafo.ponderado,
            "nodos": [
                {"id": n.id, "tipo": n.tipo, "atributos": n.atributos}
                for n in self.grafo.nodes.values()
            ],
            "aristas": [
                {
                    "origen": e.origen,
                    "destino": e.destino,
                    "monto": e.monto,
                    "timestamp": e.timestamp,
                    "n_transferencias": e.n_transferencias,
                    "comision": e.comision,
                    "costo_instalacion": e.costo_instalacion,
                    "costo_operativo": e.costo_operativo,
                    "tiempo": e.tiempo,
                    "capacidad": e.capacidad,
                    "costo_unitario": e.costo_unitario,
                    "riesgo": e.riesgo,
                    "disponible": e.disponible,
                    "canal": e.canal,
                    "atributos": e.atributos,
                }
                for e in self.grafo.iter_aristas()
            ],
        }
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

    def exportar_a_csv(self, ruta_archivo: str) -> None:
        """Exporta todas las aristas y sus atributos a formato CSV estándar."""
        os.makedirs(os.path.dirname(os.path.abspath(ruta_archivo)), exist_ok=True)
        campos = [
            "origen",
            "destino",
            "monto",
            "timestamp",
            "n_transferencias",
            "comision",
            "costo_instalacion",
            "costo_operativo",
            "tiempo",
            "capacidad",
            "costo_unitario",
            "riesgo",
            "disponible",
            "canal",
        ]
        with open(ruta_archivo, "w", encoding="utf-8", newline="") as f:
            escritor = csv.writer(f)
            escritor.writerow(campos)
            for e in self.grafo.iter_aristas():
                escritor.writerow([
                    e.origen,
                    e.destino,
                    e.monto,
                    e.timestamp or "",
                    e.n_transferencias,
                    e.comision,
                    e.costo_instalacion,
                    e.costo_operativo,
                    e.tiempo,
                    e.capacidad,
                    e.costo_unitario,
                    e.riesgo,
                    "true" if e.disponible else "false",
                    e.canal,
                ])
