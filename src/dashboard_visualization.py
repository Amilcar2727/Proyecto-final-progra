"""Interactive Plotly graph figures for the OptiFin dashboard."""

from __future__ import annotations

import html
import math
from collections.abc import Callable, Iterable, Mapping
from typing import Optional

import networkx as nx
import plotly.graph_objects as go

from src.graph import Edge, Graph
from src.visualizacion import convertir_a_networkx


GROUND = "#F8F6EF"
INK = "#26332D"
MUTED = "#657168"
GREEN = "#477653"
CLAY = "#C75B3B"
EDGE = "#9AA69B"
COMMUNITY_COLORS = (
    "#477653",
    "#557D9C",
    "#A07945",
    "#855F68",
    "#73927E",
    "#66716D",
    "#A98967",
    "#607C86",
    "#B05A45",
    "#799A83",
    "#4A636E",
    "#84794D",
)
NODE_TYPE_COLORS = {
    "cuenta": "#477653",
    "cliente": "#557D9C",
    "agencia": "#A07945",
    "boveda_central": "#855F68",
    "boveda_regional": "#73927E",
    "atm": "#607C86",
    "entidad": "#66716D",
    "plataforma_pago": "#A98967",
    "billetera": "#557D9C",
    "servidor": "#66716D",
}


def graph_positions(grafo: Graph, seed: int = 42) -> dict[str, tuple[float, float]]:
    """Return a deterministic layout that can be reused across graph states."""
    if not grafo.nodes:
        return {}

    graph = convertir_a_networkx(grafo)
    if len(graph) == 1:
        node_id = next(iter(graph.nodes))
        return {node_id: (0.0, 0.0)}

    positions = nx.spring_layout(
        graph,
        seed=seed,
        k=1.0 / (len(graph) ** 0.5 + 0.1),
        iterations=60,
        weight=None,
    )
    return {
        node_id: (float(position[0]), float(position[1]))
        for node_id, position in positions.items()
    }


def _edge_key(edge: tuple[str, str], directed: bool) -> tuple[str, str]:
    return edge if directed else tuple(sorted(edge))


def network_figure(
    grafo: Graph,
    *,
    communities: Optional[Mapping[str, int]] = None,
    highlighted_edges: Iterable[tuple[str, str]] = (),
    selected_edges: Iterable[tuple[str, str]] = (),
    selected_node: Optional[str] = None,
    measure: Optional[Callable[[Edge], float]] = None,
    measure_label: str = "Peso",
    edge_detail: Optional[Callable[[Edge], str]] = None,
    positions: Optional[Mapping[str, tuple[float, float]]] = None,
    display_labels: Optional[Mapping[str, str]] = None,
    height: int = 520,
) -> go.Figure:
    """Render a graph with stable positions, explicit legends, and useful hover data."""
    figure = go.Figure()
    node_ids = list(grafo.nodes)

    if not node_ids:
        figure.add_annotation(
            text="No hay nodos para mostrar.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": MUTED, "size": 15},
        )
        figure.update_layout(
            height=height,
            margin={"l": 8, "r": 8, "t": 8, "b": 8},
            paper_bgcolor=GROUND,
            plot_bgcolor=GROUND,
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return figure

    layout_positions = dict(positions or {})
    if not all(node_id in layout_positions for node_id in node_ids):
        layout_positions.update(graph_positions(grafo))
    labels = display_labels or {}
    highlighted = {_edge_key(edge, grafo.dirigido) for edge in highlighted_edges}
    selected = {_edge_key(edge, grafo.dirigido) for edge in selected_edges}
    edges = list(grafo.iter_aristas())
    values = [
        max(0.0, float(measure(edge))) if measure is not None else 1.0
        for edge in edges
    ]
    max_value = max(values, default=0.0)
    max_value = max_value or 1.0
    legend_names: set[str] = set()

    for edge, value in zip(edges, values):
        source = edge.origen
        destination = edge.destino
        pair = _edge_key((source, destination), grafo.dirigido)
        is_selected = pair in selected
        is_highlighted = pair in highlighted
        color = CLAY if is_selected else GREEN if is_highlighted else EDGE
        width = 1.2 + 2.4 * math.sqrt(value / max_value)
        x0, y0 = layout_positions[source]
        x1, y1 = layout_positions[destination]
        detail = edge_detail(edge) if edge_detail is not None else (
            f"{measure_label}: {value:,.2f}" if measure is not None else measure_label
        )
        safe_source = html.escape(labels.get(source, source))
        safe_destination = html.escape(labels.get(destination, destination))
        safe_detail = html.escape(detail)

        figure.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"color": color, "width": width},
                hovertemplate=(
                    f"<b>{safe_source} → {safe_destination}</b>"
                    f"<br>{safe_detail}<extra></extra>"
                ),
                showlegend=False,
                name="Enlace",
            )
        )

        if grafo.dirigido and source != destination:
            figure.add_annotation(
                x=x0 * 0.2 + x1 * 0.8,
                y=y0 * 0.2 + y1 * 0.8,
                ax=x0 * 0.8 + x1 * 0.2,
                ay=y0 * 0.8 + y1 * 0.2,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=0.65,
                arrowwidth=1,
                arrowcolor=color,
                opacity=0.72,
            )

    community_ids = sorted(set(communities.values())) if communities else []
    community_color = {
        community_id: COMMUNITY_COLORS[index % len(COMMUNITY_COLORS)]
        for index, community_id in enumerate(community_ids)
    }
    node_colors = [
        community_color.get(communities.get(node_id), NODE_TYPE_COLORS.get(
            grafo.nodes[node_id].tipo, MUTED
        ))
        if communities is not None
        else NODE_TYPE_COLORS.get(grafo.nodes[node_id].tipo, MUTED)
        for node_id in node_ids
    ]
    degrees = [grafo.grado(node_id) for node_id in node_ids]
    sizes = [min(31, 16 + degree * 1.1) for degree in degrees]
    node_line_colors = [CLAY if node_id == selected_node else GROUND for node_id in node_ids]
    node_line_widths = [3 if node_id == selected_node else 1.2 for node_id in node_ids]
    node_customdata = [
        [
            html.escape(labels.get(node_id, node_id)),
            html.escape(grafo.nodes[node_id].tipo.replace("_", " ")),
            degree,
            (
                f"C-{communities[node_id]}"
                if communities is not None and node_id in communities
                else "No evaluada" if communities is not None
                else "—"
            ),
        ]
        for node_id, degree in zip(node_ids, degrees)
    ]

    figure.add_trace(
        go.Scatter(
            x=[layout_positions[node_id][0] for node_id in node_ids],
            y=[layout_positions[node_id][1] for node_id in node_ids],
            mode="markers+text",
            text=[
                html.escape(labels.get(node_id, node_id)) if node_id == selected_node else ""
                for node_id in node_ids
            ],
            textposition="top center",
            textfont={"size": 11, "color": INK},
            customdata=node_customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Tipo: %{customdata[1]}<br>"
                "Grado: %{customdata[2]}<br>"
                "Comunidad: %{customdata[3]}<extra></extra>"
            ),
            marker={
                "size": sizes,
                "color": node_colors,
                "line": {"color": node_line_colors, "width": node_line_widths},
                "opacity": 0.96,
            },
            showlegend=False,
            name="Nodos",
        )
    )

    if community_ids:
        for community_id in community_ids:
            figure.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker={"size": 9, "color": community_color[community_id]},
                    name=f"Comunidad {community_id}",
                    hoverinfo="skip",
                    showlegend=True,
                )
            )
    else:
        node_types = sorted({grafo.nodes[node_id].tipo for node_id in node_ids})
        for node_type in node_types:
            figure.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker={"size": 9, "color": NODE_TYPE_COLORS.get(node_type, MUTED)},
                    name=node_type.replace("_", " ").capitalize(),
                    hoverinfo="skip",
                    showlegend=True,
                )
            )

    figure.update_layout(
        height=height,
        margin={"l": 12, "r": 12, "t": 14, "b": 14},
        paper_bgcolor=GROUND,
        plot_bgcolor=GROUND,
        hoverlabel={"bgcolor": INK, "font": {"color": "#F8F6EF"}},
        hovermode="closest",
        dragmode="pan",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.12,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11, "color": INK},
        },
        xaxis={"visible": False, "scaleanchor": "y", "scaleratio": 1},
        yaxis={"visible": False},
    )
    return figure
