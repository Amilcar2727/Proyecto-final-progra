"""
Módulo de visualización gráfica de redes financieras utilizando Matplotlib y NetworkX (solo para layout).
Permite renderizar grafos, colorear por tipo de nodo, destacar comunidades detectadas,
resaltar aristas del Árbol de Expansión Mínima (MST) y señalar cuellos de botella del corte mínimo.
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Set, Tuple
import matplotlib
matplotlib.use("Agg")  # Backend no interactivo para entornos headless y tests
import matplotlib.pyplot as plt
import networkx as nx

from src.graph import Graph

# Paleta de colores por tipo de nodo financiero
COLORES_TIPO_NODO = {
    "cuenta": "#4A90E2",           # Azul acero
    "cliente": "#50E3C2",          # Turquesa
    "agencia": "#F5A623",          # Ámbar
    "boveda_central": "#D0021B",    # Rojo carmesí
    "boveda_regional": "#BD10E0",   # Púrpura
    "atm": "#7ED321",              # Verde lima
    "entidad": "#9013FE",          # Violeta
    "plataforma_pago": "#FF6F00",   # Naranja fuerte
    "billetera": "#00BCD4",        # Cyan
    "servidor": "#607D8B",         # Gris azulado
}

COLORES_COMUNIDADES = [
    "#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00",
    "#FFFF33", "#A65628", "#F781BF", "#999999", "#66C2A5"
]


def convertir_a_networkx(grafo: Graph) -> nx.DiGraph | nx.Graph:
    """Convierte la estructura interna Graph a un objeto NetworkX para layout visual."""
    g_nx = nx.DiGraph() if grafo.dirigido else nx.Graph()
    for n in grafo.nodes.values():
        g_nx.add_node(n.id, tipo=n.tipo, **n.atributos)
    for e in grafo.iter_aristas():
        g_nx.add_edge(e.origen, e.destino, monto=e.monto, capacidad=e.capacidad)
    return g_nx


def graficar_red_financiera(
    grafo: Graph,
    titulo: str = "Red Financiera - OptiFin",
    comunidades: Optional[Dict[str, int]] = None,
    aristas_destacadas: Optional[List[Tuple[str, str]]] = None,
    etiqueta_destacadas: str = "Destacadas",
    color_destacadas: str = "#E74C3C",
    ruta_guardado: Optional[str] = None,
    tamano_figura: Tuple[int, int] = (12, 9),
) -> plt.Figure:
    """
    Renderiza gráficamente la red financiera con estilos contextuales.

    Args:
        grafo: Instancia de Graph de OptiFin.
        titulo: Título principal del gráfico.
        comunidades: Diccionario opcional {id_nodo: id_comunidad} para colorear por cluster.
        aristas_destacadas: Lista de tuplas (u, v) para resaltar (ej. MST o corte mínimo).
        etiqueta_destacadas: Nombre de la leyenda para aristas destacadas.
        color_destacadas: Color hexadecimal de las aristas destacadas.
        ruta_guardado: Ruta donde guardar el archivo .png generado.
        tamano_figura: Dimensiones (ancho, alto) de la imagen.

    Returns:
        Objeto matplotlib.figure.Figure.
    """
    g_nx = convertir_a_networkx(grafo)
    fig, ax = plt.subplots(figsize=tamano_figura)

    if len(g_nx.nodes) == 0:
        ax.text(0.5, 0.5, "Red Vacía", ha="center", va="center", fontsize=14)
        ax.axis("off")
        if ruta_guardado:
            os.makedirs(os.path.dirname(os.path.abspath(ruta_guardado)), exist_ok=True)
            plt.savefig(ruta_guardado, bbox_inches="tight", dpi=150)
        return fig

    # Cálculo de layout usando spring_layout determinista
    pos = nx.spring_layout(g_nx, seed=42, k=1.0 / (len(g_nx.nodes) ** 0.5 + 0.1))

    # Determinación de colores de nodos
    node_colors = []
    for node_id in g_nx.nodes():
        if comunidades and node_id in comunidades:
            cid = comunidades[node_id]
            node_colors.append(COLORES_COMUNIDADES[cid % len(COLORES_COMUNIDADES)])
        else:
            tipo = grafo.nodes[node_id].tipo if node_id in grafo.nodes else "cuenta"
            node_colors.append(COLORES_TIPO_NODO.get(tipo, "#4A90E2"))

    # Dibujar aristas estándar
    aristas_set = set()
    if aristas_destacadas:
        for u, v in aristas_destacadas:
            aristas_set.add((u, v))
            if not grafo.dirigido:
                aristas_set.add((v, u))

    aristas_normales = [
        (u, v) for u, v in g_nx.edges()
        if (u, v) not in aristas_set
    ]

    nx.draw_networkx_nodes(
        g_nx, pos, node_color=node_colors, node_size=600, edgecolors="#2C3E50", linewidths=1.5, ax=ax
    )
    nx.draw_networkx_edges(
        g_nx, pos, edgelist=aristas_normales, edge_color="#BDC3C7", width=1.2, alpha=0.7, ax=ax,
        arrows=grafo.dirigido, arrowsize=14
    )

    # Dibujar aristas destacadas si existen
    if aristas_destacadas:
        aristas_dest_validas = [
            (u, v) for u, v in aristas_destacadas
            if g_nx.has_edge(u, v) or (not grafo.dirigido and g_nx.has_edge(v, u))
        ]
        nx.draw_networkx_edges(
            g_nx, pos, edgelist=aristas_dest_validas, edge_color=color_destacadas, width=2.8, ax=ax,
            arrows=grafo.dirigido, arrowsize=16
        )

    # Etiquetas de nodos
    nx.draw_networkx_labels(g_nx, pos, font_size=9, font_family="sans-serif", font_weight="bold", ax=ax)

    ax.set_title(titulo, fontsize=14, fontweight="bold", pad=15)
    ax.axis("off")

    if ruta_guardado:
        os.makedirs(os.path.dirname(os.path.abspath(ruta_guardado)), exist_ok=True)
        plt.savefig(ruta_guardado, bbox_inches="tight", dpi=150)

    plt.close(fig)
    return fig
