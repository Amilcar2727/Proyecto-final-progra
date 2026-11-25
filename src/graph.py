"""
Módulo de estructura de datos de grafos para redes financieras.
Implementación de las clases Node, Edge y Graph usando listas de adyacencia.

Complejidades generales:
- Espacio: O(V + E)
- Consulta de vecinos: O(deg(v))
- Adición de nodo / arista: O(1) amortizado
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple


TIPOS_NODO_VALIDOS = {
    "cuenta",
    "cliente",
    "agencia",
    "boveda_central",
    "boveda_regional",
    "atm",
    "entidad",
    "plataforma_pago",
    "billetera",
    "servidor",
}


@dataclass
class Node:
    """
    Representa una entidad o punto transaccional en la red financiera.

    Atributos:
        id: Identificador único del nodo.
        tipo: Tipo de entidad financiera (debe pertenecer a TIPOS_NODO_VALIDOS).
        atributos: Diccionario libre para oferta, demanda, región, etc.
    """

    id: str
    tipo: str = "cuenta"
    atributos: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_NODO_VALIDOS:
            raise ValueError(
                f"Tipo de nodo '{self.tipo}' no válido. Permitidos: {sorted(TIPOS_NODO_VALIDOS)}"
            )

    def get(self, clave: str, defecto: Any = None) -> Any:
        """Obtiene un atributo libre del nodo."""
        return self.atributos.get(clave, defecto)

    def set(self, clave: str, valor: Any) -> None:
        """Establece un atributo libre del nodo."""
        self.atributos[clave] = valor


@dataclass
class Edge:
    """
    Representa una conexión financiera, canal de distribución o enlace de red.

    Atributos:
        origen: ID del nodo emisor/origen.
        destino: ID del nodo receptor/destino.
        monto: Monto transaccional o volumen de fondos.
        timestamp: Marca de tiempo ISO o época de la operación.
        n_transferencias: Cantidad de transferencias agregadas.
        comision: Costo o comisión operativa directa.
        costo_instalacion: Inversión en despliegue de enlace.
        costo_operativo: Costo recurrente de mantenimiento/operación.
        tiempo: Latencia o tiempo estimado de tránsito/procesamiento.
        capacidad: Límite superior de flujo o transporte.
        costo_unitario: Costo por unidad de flujo transportado.
        riesgo: Probabilidad o índice de riesgo en rango [0.0, 1.0].
        disponible: Bandera de operatividad del enlace.
        canal: Medio transaccional (SPEI, SWIFT, Blindado, Fibra, etc.).
        atributos: Metadatos adicionales.
    """

    origen: str
    destino: str
    monto: float = 0.0
    timestamp: Optional[str] = None
    n_transferencias: int = 1
    comision: float = 0.0
    costo_instalacion: float = 0.0
    costo_operativo: float = 0.0
    tiempo: float = 0.0
    capacidad: float = 0.0
    costo_unitario: float = 0.0
    riesgo: float = 0.0
    disponible: bool = True
    canal: str = "general"
    atributos: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.monto < 0:
            raise ValueError(f"El monto no puede ser negativo: {self.monto}")
        if self.n_transferencias < 0:
            raise ValueError(f"El número de transferencias no puede ser negativo: {self.n_transferencias}")
        if self.capacidad < 0:
            raise ValueError(f"La capacidad no puede ser negativa: {self.capacidad}")
        if not (0.0 <= self.riesgo <= 1.0):
            raise ValueError(f"El riesgo debe estar acotado en [0, 1], valor recibido: {self.riesgo}")


class Graph:
    """
    Estructura de grafo financiero basada en listas de adyacencia.

    Almacena nodos en un diccionario {id: Node} y aristas como
    dict[str, dict[str, list[Edge]]] para soportar multigrafos transaccionales.

    Complejidad temporal:
    - Agregar/modificar nodo: O(1)
    - Eliminar nodo: O(deg(v) + deg_in(v))
    - Agregar arista: O(1)
    - Consultar vecinos: O(deg(v))
    - Espacio: O(V + E)
    """

    def __init__(self, dirigido: bool = True, ponderado: bool = True) -> None:
        self.dirigido: bool = dirigido
        self.ponderado: bool = ponderado
        self.nodes: Dict[str, Node] = {}
        # adj[u][v] = lista de aristas de u a v
        self.adj: Dict[str, Dict[str, List[Edge]]] = {}
        # in_adj[v][u] = lista de aristas de u a v (acelera grado de entrada y borrado)
        self.in_adj: Dict[str, Dict[str, List[Edge]]] = {}

    def agregar_nodo(self, nodo: Node) -> None:
        """
        Agrega un nodo al grafo. Si ya existe, actualiza sus atributos.
        Complejidad: O(1) tiempo, O(1) espacio.
        """
        if nodo.id not in self.nodes:
            self.nodes[nodo.id] = nodo
            self.adj[nodo.id] = {}
            self.in_adj[nodo.id] = {}
        else:
            self.nodes[nodo.id] = nodo

    def obtener_nodo(self, nodo_id: str) -> Node:
        """Retorna el objeto Node correspondiente al ID."""
        if nodo_id not in self.nodes:
            raise KeyError(f"Nodo '{nodo_id}' no encontrado en el grafo.")
        return self.nodes[nodo_id]

    def existe_nodo(self, nodo_id: str) -> bool:
        """Verifica si un nodo pertenece al grafo en O(1)."""
        return nodo_id in self.nodes

    def modificar_nodo(self, nodo_id: str, tipo: Optional[str] = None, **atributos: Any) -> None:
        """
        Modifica el tipo o atributos de un nodo existente en O(1).
        """
        nodo = self.obtener_nodo(nodo_id)
        if tipo is not None:
            if tipo not in TIPOS_NODO_VALIDOS:
                raise ValueError(f"Tipo '{tipo}' inválido.")
            nodo.tipo = tipo
        for k, v in atributos.items():
            nodo.atributos[k] = v

    def eliminar_nodo(self, nodo_id: str) -> None:
        """
        Elimina un nodo y todas las aristas conectadas (incidentes y emergentes).
        Complejidad: O(deg_out(v) + deg_in(v)).
        """
        if nodo_id not in self.nodes:
            raise KeyError(f"Nodo '{nodo_id}' no existe.")

        # Eliminar referencias en destinos (aristas salientes de nodo_id)
        for dest in list(self.adj[nodo_id].keys()):
            if dest in self.in_adj and nodo_id in self.in_adj[dest]:
                del self.in_adj[dest][nodo_id]

        # Eliminar referencias en orígenes (aristas entrantes hacia nodo_id)
        for orig in list(self.in_adj[nodo_id].keys()):
            if orig in self.adj and nodo_id in self.adj[orig]:
                del self.adj[orig][nodo_id]

        del self.adj[nodo_id]
        del self.in_adj[nodo_id]
        del self.nodes[nodo_id]

    def agregar_arista(self, arista: Edge) -> None:
        """
        Registra una arista en el grafo. Si los nodos extremos no existen,
        los inicializa automáticamente con tipo 'cuenta'.
        Si el grafo es no dirigido, crea además la arista inversa simétrica.
        Complejidad: O(1).
        """
        if arista.origen not in self.nodes:
            self.agregar_nodo(Node(id=arista.origen, tipo="cuenta"))
        if arista.destino not in self.nodes:
            self.agregar_nodo(Node(id=arista.destino, tipo="cuenta"))

        if arista.destino not in self.adj[arista.origen]:
            self.adj[arista.origen][arista.destino] = []
        self.adj[arista.origen][arista.destino].append(arista)

        if arista.origen not in self.in_adj[arista.destino]:
            self.in_adj[arista.destino][arista.origen] = []
        self.in_adj[arista.destino][arista.origen].append(arista)

        if not self.dirigido and arista.origen != arista.destino:
            arista_rev = Edge(
                origen=arista.destino,
                destino=arista.origen,
                monto=arista.monto,
                timestamp=arista.timestamp,
                n_transferencias=arista.n_transferencias,
                comision=arista.comision,
                costo_instalacion=arista.costo_instalacion,
                costo_operativo=arista.costo_operativo,
                tiempo=arista.tiempo,
                capacidad=arista.capacidad,
                costo_unitario=arista.costo_unitario,
                riesgo=arista.riesgo,
                disponible=arista.disponible,
                canal=arista.canal,
                atributos=dict(arista.atributos),
            )
            if arista_rev.destino not in self.adj[arista_rev.origen]:
                self.adj[arista_rev.origen][arista_rev.destino] = []
            self.adj[arista_rev.origen][arista_rev.destino].append(arista_rev)

            if arista_rev.origen not in self.in_adj[arista_rev.destino]:
                self.in_adj[arista_rev.destino][arista_rev.origen] = []
            self.in_adj[arista_rev.destino][arista_rev.origen].append(arista_rev)

    def eliminar_arista(
        self, origen: str, destino: str, arista: Optional[Edge] = None
    ) -> bool:
        """
        Elimina aristas entre origen y destino. Si se especifica arista, borra
        únicamente esa instancia; si es None, elimina todas entre ambos nodos.
        Complejidad: O(k) donde k es el número de aristas paralelas entre u y v.
        """
        if origen not in self.adj or destino not in self.adj[origen]:
            return False

        if arista is None:
            del self.adj[origen][destino]
            if destino in self.in_adj and origen in self.in_adj[destino]:
                del self.in_adj[destino][origen]
            if not self.dirigido and destino in self.adj and origen in self.adj[destino]:
                del self.adj[destino][origen]
                if origen in self.in_adj and destino in self.in_adj[origen]:
                    del self.in_adj[origen][destino]
            return True

        if arista in self.adj[origen][destino]:
            self.adj[origen][destino].remove(arista)
            if not self.adj[origen][destino]:
                del self.adj[origen][destino]
            if destino in self.in_adj and origen in self.in_adj[destino]:
                if arista in self.in_adj[destino][origen]:
                    self.in_adj[destino][origen].remove(arista)
                if not self.in_adj[destino][origen]:
                    del self.in_adj[destino][origen]

            if not self.dirigido:
                # Localizar y remover inversa
                if destino in self.adj and origen in self.adj[destino]:
                    inversas = [
                        e for e in self.adj[destino][origen]
                        if e.monto == arista.monto and e.timestamp == arista.timestamp
                    ]
                    if inversas:
                        inv = inversas[0]
                        self.adj[destino][origen].remove(inv)
                        if not self.adj[destino][origen]:
                            del self.adj[destino][origen]
                        if origen in self.in_adj and destino in self.in_adj[origen]:
                            if inv in self.in_adj[origen][destino]:
                                self.in_adj[origen][destino].remove(inv)
                            if not self.in_adj[origen][destino]:
                                del self.in_adj[origen][destino]
            return True
        return False

    def obtener_aristas(self, origen: str, destino: str) -> List[Edge]:
        """Retorna lista de aristas entre origen y destino."""
        return self.adj.get(origen, {}).get(destino, [])

    def vecinos(self, nodo_id: str) -> List[str]:
        """Retorna lista de IDs de nodos vecinos salientes."""
        return list(self.adj.get(nodo_id, {}).keys())

    def predecesores(self, nodo_id: str) -> List[str]:
        """Retorna lista de IDs de nodos con aristas dirigidas hacia nodo_id."""
        return list(self.in_adj.get(nodo_id, {}).keys())

    def grado_salida(self, nodo_id: str) -> int:
        """Número de aristas salientes desde nodo_id."""
        return sum(len(edges) for edges in self.adj.get(nodo_id, {}).values())

    def grado_entrada(self, nodo_id: str) -> int:
        """Número de aristas entrantes a nodo_id."""
        return sum(len(edges) for edges in self.in_adj.get(nodo_id, {}).values())

    def grado(self, nodo_id: str) -> int:
        """Grado total del nodo."""
        if not self.dirigido:
            # En no dirigido, adj contiene todas las aristas incidentes
            # Lazos cuentan 2
            deg = 0
            for v, edges in self.adj.get(nodo_id, {}).items():
                if v == nodo_id:
                    deg += 2 * len(edges)
                else:
                    deg += len(edges)
            return deg
        return self.grado_salida(nodo_id) + self.grado_entrada(nodo_id)

    @property
    def num_nodos(self) -> int:
        return len(self.nodes)

    @property
    def num_aristas(self) -> int:
        total = sum(
            len(edges)
            for orig_adj in self.adj.values()
            for edges in orig_adj.values()
        )
        if not self.dirigido:
            # Cada arista u-v con u!=v se cuenta dos veces en adj
            lazos = sum(
                len(self.adj[u].get(u, []))
                for u in self.nodes
            )
            return (total - lazos) // 2 + lazos
        return total

    def iter_aristas(self) -> Iterator[Edge]:
        """
        Generador para recorrer todas las aristas del grafo.
        En grafos no dirigidos, produce cada conexión única una sola vez (u <= v).
        """
        vistos: Set[Tuple[str, str, int]] = set()
        for u, vecinos in self.adj.items():
            for v, aristas in vecinos.items():
                for idx, edge in enumerate(aristas):
                    if not self.dirigido:
                        clave = (min(u, v), max(u, v), idx) if u != v else (u, v, idx)
                        if clave in vistos:
                            continue
                        vistos.add(clave)
                    yield edge

    def transpuesto(self) -> Graph:
        """
        Construye el grafo transpuesto (invirtiendo la dirección de cada arista).
        Complejidad: O(V + E) tiempo y espacio.
        """
        gt = Graph(dirigido=self.dirigido, ponderado=self.ponderado)
        for n in self.nodes.values():
            gt.agregar_nodo(Node(id=n.id, tipo=n.tipo, atributos=dict(n.atributos)))

        for u, vecinos in self.adj.items():
            for v, aristas in vecinos.items():
                for e in aristas:
                    gt.agregar_arista(
                        Edge(
                            origen=v,
                            destino=u,
                            monto=e.monto,
                            timestamp=e.timestamp,
                            n_transferencias=e.n_transferencias,
                            comision=e.comision,
                            costo_instalacion=e.costo_instalacion,
                            costo_operativo=e.costo_operativo,
                            tiempo=e.tiempo,
                            capacidad=e.capacidad,
                            costo_unitario=e.costo_unitario,
                            riesgo=e.riesgo,
                            disponible=e.disponible,
                            canal=e.canal,
                            atributos=dict(e.atributos),
                        )
                    )
        return gt

    def copiar(self) -> Graph:
        """Retorna una copia profunda e independiente del grafo."""
        copia = Graph(dirigido=self.dirigido, ponderado=self.ponderado)
        for n in self.nodes.values():
            copia.agregar_nodo(Node(id=n.id, tipo=n.tipo, atributos=dict(n.atributos)))
        for edge in self.iter_aristas():
            copia.agregar_arista(
                Edge(
                    origen=edge.origen,
                    destino=edge.destino,
                    monto=edge.monto,
                    timestamp=edge.timestamp,
                    n_transferencias=edge.n_transferencias,
                    comision=edge.comision,
                    costo_instalacion=edge.costo_instalacion,
                    costo_operativo=edge.costo_operativo,
                    tiempo=edge.tiempo,
                    capacidad=edge.capacidad,
                    costo_unitario=edge.costo_unitario,
                    riesgo=edge.riesgo,
                    disponible=edge.disponible,
                    canal=edge.canal,
                    atributos=dict(edge.atributos),
                )
            )
        return copia

    def subgrafo(
        self,
        filtro_nodos: Optional[Callable[[Node], bool]] = None,
        filtro_aristas: Optional[Callable[[Edge], bool]] = None,
    ) -> Graph:
        """
        Genera un subgrafo inducido filtrando nodos y/o aristas.
        Complejidad: O(V + E).
        """
        sub = Graph(dirigido=self.dirigido, ponderado=self.ponderado)
        nodos_validos: Set[str] = set()

        for nodo in self.nodes.values():
            if filtro_nodos is None or filtro_nodos(nodo):
                sub.agregar_nodo(Node(id=nodo.id, tipo=nodo.tipo, atributos=dict(nodo.atributos)))
                nodos_validos.add(nodo.id)

        for edge in self.iter_aristas():
            if edge.origen in nodos_validos and edge.destino in nodos_validos:
                if filtro_aristas is None or filtro_aristas(edge):
                    sub.agregar_arista(
                        Edge(
                            origen=edge.origen,
                            destino=edge.destino,
                            monto=edge.monto,
                            timestamp=edge.timestamp,
                            n_transferencias=edge.n_transferencias,
                            comision=edge.comision,
                            costo_instalacion=edge.costo_instalacion,
                            costo_operativo=edge.costo_operativo,
                            tiempo=edge.tiempo,
                            capacidad=edge.capacidad,
                            costo_unitario=edge.costo_unitario,
                            riesgo=edge.riesgo,
                            disponible=edge.disponible,
                            canal=edge.canal,
                            atributos=dict(edge.atributos),
                        )
                    )
        return sub

    def a_no_dirigido(
        self,
        agregar: Callable[[List[float]], float] = sum,
        peso_attr: str = "monto",
    ) -> Graph:
        """
        Colapsa el grafo en un grafo NO dirigido, consolidando transferencias
        bidireccionales A->B y B->A en una única arista no dirigida con peso agregado.

        Complejidad: O(V + E) tiempo y espacio.
        """
        g_nd = Graph(dirigido=False, ponderado=self.ponderado)
        for n in self.nodes.values():
            g_nd.agregar_nodo(Node(id=n.id, tipo=n.tipo, atributos=dict(n.atributos)))

        # Agrupar aristas por par no ordenado
        pares: Dict[Tuple[str, str], List[Edge]] = {}
        for edge in self.iter_aristas():
            u, v = sorted([edge.origen, edge.destino])
            par = (u, v)
            if par not in pares:
                pares[par] = []
            pares[par].append(edge)

        for (u, v), aristas in pares.items():
            montos = [e.monto for e in aristas]
            transfers = sum(e.n_transferencias for e in aristas)
            peso_agregado = agregar(montos) if montos else 0.0
            comision_total = sum(e.comision for e in aristas)
            tiempo_promedio = sum(e.tiempo for e in aristas) / len(aristas) if aristas else 0.0
            capacidad_total = sum(e.capacidad for e in aristas)
            riesgo_max = max((e.riesgo for e in aristas), default=0.0)

            nueva_arista = Edge(
                origen=u,
                destino=v,
                monto=peso_agregado,
                n_transferencias=transfers,
                comision=comision_total,
                tiempo=tiempo_promedio,
                capacidad=capacidad_total,
                riesgo=riesgo_max,
                disponible=all(e.disponible for e in aristas),
                canal="consolidado",
            )
            g_nd.agregar_arista(nueva_arista)

        return g_nd

    def obtener_vista_ponderada(
        self, peso_fn: Callable[[Edge], float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Retorna una vista simplificada {u: {v: peso}} calculada con peso_fn.
        Si hay múltiples aristas entre u y v, toma la arista de mínimo peso.
        """
        vista: Dict[str, Dict[str, float]] = {u: {} for u in self.nodes}
        for u in self.nodes:
            for v, aristas in self.adj.get(u, {}).items():
                if aristas:
                    min_w = min(peso_fn(e) for e in aristas)
                    vista[u][v] = min_w
        return vista
