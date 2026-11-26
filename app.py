"""OptiFin's local Streamlit interface for exploring its graph scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analisis_transacciones import AnalizadorTransaccionesFinancieras
from src.distribucion_liquidez import (
    ID_SUPER_FUENTE,
    ID_SUPER_SUMIDERO,
    PlanificadorDistribucionLiquidez,
)
from src.enrutamiento_financiero import OptimizadorRedTroncal
from src.gestion_red import ErrorRedFinanciera, GestorRedFinanciera
from src.graph import Edge, Graph
from src.dashboard_visualization import (
    CLAY,
    GREEN,
    GROUND,
    INK,
    MUTED,
    graph_positions,
    network_figure,
)


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
COMMUNITY_DATA = "transacciones.json"
BACKBONE_DATA = "red_troncal.json"
LIQUIDITY_DATA = "distribucion_liquidez.json"

MODULES = (
    "Comunidades",
    "Red troncal",
    "Distribución de liquidez",
)


@st.cache_resource(show_spinner=False)
def load_graph(filename: str) -> Graph:
    path = DATA_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"No existe {path.name}. Ejecuta `python scripts/generar_datos.py` "
            "desde la carpeta del proyecto para regenerar los datos."
        )
    manager = GestorRedFinanciera()
    return manager.cargar_desde_json(str(path), estricto=False)


@st.cache_data(show_spinner=False)
def load_dataset(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"No existe {path.name}. Ejecuta `python scripts/generar_datos.py` "
            "desde la carpeta del proyecto para regenerar los datos."
        )
    with path.open(encoding="utf-8") as data_file:
        data = json.load(data_file)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} debe contener un objeto JSON.")
    return data


def show_data_error(error: Exception) -> None:
    st.error(f"No se pudo cargar el conjunto de datos: {error}")
    st.stop()


def resolve_module_params(
    module_key: str,
    pending_params: dict[str, Any],
    *,
    submitted: bool = False,
) -> tuple[dict[str, Any], int]:
    applied_key = f"{module_key}_applied_params"
    rev_key = f"{module_key}_revision"

    if applied_key not in st.session_state:
        st.session_state[applied_key] = dict(pending_params)
    if rev_key not in st.session_state:
        st.session_state[rev_key] = 0

    if submitted:
        load_graph.clear()
        load_dataset.clear()
        st.session_state[applied_key] = dict(pending_params)
        st.session_state[rev_key] += 1
        st.toast("Resultados actualizados con los parámetros seleccionados.")

    return st.session_state[applied_key], st.session_state[rev_key]


def render_module_header(
    module_key: str,
    title: str,
    subtitle: str,
    pending_params: dict[str, Any],
    submitted: bool,
) -> tuple[dict[str, Any], int]:
    st.title(title)
    st.caption(subtitle)
    return resolve_module_params(
        module_key,
        pending_params,
        submitted=submitted,
    )


def selected_row(key: str, rows: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    state = st.session_state.get(key)
    selection = getattr(state, "selection", None)
    indexes = getattr(selection, "rows", [])
    if not indexes or not 0 <= indexes[0] < len(rows):
        return None
    return rows[indexes[0]]


def selected_pair(row: Optional[dict[str, Any]]) -> list[tuple[str, str]]:
    if row is None:
        return []
    origin = row.get("Origen")
    destination = row.get("Destino")
    if not origin or not destination:
        return []
    return [(str(origin), str(destination))]


def money(value: float) -> str:
    return f"${value:,.0f}"


def format_table(
    rows: list[dict[str, Any]],
    *,
    key: str,
    height: int = 330,
) -> None:
    frame = pd.DataFrame(rows)
    st.dataframe(
        frame,
        key=key,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        use_container_width=True,
        height=height,
    )


def comparison_figure(
    labels: list[str],
    values: list[float],
    *,
    title: str,
    value_label: str,
    colors: Optional[list[str]] = None,
    decimals: int = 3,
) -> go.Figure:
    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors or [GREEN] * len(labels),
            text=[f"{value:,.{decimals}f}" for value in values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                f"%{{y}}<br>{value_label}: %{{x:,.{decimals}f}}<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title={"text": title, "font": {"size": 16, "color": INK}},
        height=max(190, 62 * len(labels)),
        margin={"l": 12, "r": 30, "t": 48, "b": 14},
        paper_bgcolor=GROUND,
        plot_bgcolor=GROUND,
        showlegend=False,
        xaxis={"showgrid": True, "gridcolor": "#DCD9CF", "zeroline": False},
        yaxis={"autorange": "reversed", "showgrid": False},
        font={"color": INK, "family": "Arial, sans-serif", "size": 12},
    )
    return figure


def flow_positions(grafo: Graph) -> dict[str, tuple[float, float]]:
    layers: dict[int, list[str]] = {layer: [] for layer in range(5)}
    for node_id, node in grafo.nodes.items():
        if node_id == ID_SUPER_FUENTE:
            layer = 0
        elif node_id == ID_SUPER_SUMIDERO:
            layer = 4
        elif node.tipo == "boveda_central":
            layer = 1
        elif node.tipo == "boveda_regional":
            layer = 2
        else:
            layer = 3
        layers[layer].append(node_id)

    positions: dict[str, tuple[float, float]] = {}
    for layer, node_ids in layers.items():
        ordered_ids = sorted(node_ids)
        if not ordered_ids:
            continue
        if len(ordered_ids) == 1:
            verticals = [0.0]
        else:
            verticals = [
                1.0 - 2.0 * index / (len(ordered_ids) - 1)
                for index in range(len(ordered_ids))
            ]
        positions.update({
            node_id: (float(layer), vertical)
            for node_id, vertical in zip(ordered_ids, verticals)
        })
    return positions


def run_communities() -> None:
    with st.sidebar:
        with st.form(key="communities_form"):
            st.subheader("Vista")
            algorithm_label = st.selectbox(
                "Partición visible",
                ("Louvain", "Componentes por umbral", "Propagación de etiquetas"),
            )
            graph_label = st.selectbox("Red", ("Red analizada", "Red original"))
            with st.expander("Ajustes de análisis"):
                criterion_label = st.selectbox(
                    "Peso de las transferencias",
                    ("Combinado", "Monto", "Número de transferencias"),
                )
                window_days = st.slider("Ventana temporal (días)", 0, 90, 30)
                hub_percentile = st.slider("Percentil de concentradores", 80, 100, 92)
                hub_action_label = st.selectbox(
                    "Tratamiento de concentradores",
                    ("Excluir", "Limitar su peso"),
                )
                runs = st.slider("Corridas Louvain", 1, 10, 5)
                threshold = st.slider("Umbral para línea base", 0.0, 10.0, 3.0, 0.5)
            submitted = st.form_submit_button(
                "Actualizar resultados",
                type="primary",
                use_container_width=True,
            )

    pending_params = {
        "algorithm_label": algorithm_label,
        "graph_label": graph_label,
        "criterion_label": criterion_label,
        "window_days": window_days,
        "hub_percentile": hub_percentile,
        "hub_action_label": hub_action_label,
        "runs": runs,
        "threshold": threshold,
    }
    params, revision = render_module_header(
        "communities",
        "Comunidades financieras",
        "Datos sintéticos · semilla 42 · indicadores para revisión",
        pending_params,
        submitted,
    )

    algorithm_label = params["algorithm_label"]
    graph_label = params["graph_label"]
    criterion_label = params["criterion_label"]
    window_days = params["window_days"]
    hub_percentile = params["hub_percentile"]
    hub_action_label = params["hub_action_label"]
    runs = params["runs"]
    threshold = params["threshold"]

    criterion = {
        "Combinado": "combinado",
        "Monto": "monto",
        "Número de transferencias": "transferencias",
    }[criterion_label]

    try:
        graph = load_graph(COMMUNITY_DATA)
    except (OSError, ValueError, ErrorRedFinanciera) as error:
        show_data_error(error)
        return

    analyst = AnalizadorTransaccionesFinancieras(
        criterio_peso=criterion,
        ventana_dias=window_days or None,
        percentil_concentrador=float(hub_percentile),
    )
    hub_action = "excluir" if hub_action_label == "Excluir" else "limitar"
    analyzed_graph = analyst.preprocesar_red(graph, accion_concentrador=hub_action)

    with st.spinner("Calculando comunidades y líneas base..."):
        louvain = analyst.detectar_comunidades_louvain(
            analyzed_graph,
            n_corridas=runs,
            semilla=42,
        )
        baselines = analyst.detectar_lineas_base(
            analyzed_graph,
            umbral_peso=threshold,
            semilla=42,
        )

    partition_options = {
        "Louvain": louvain["particion"],
        "Componentes por umbral": baselines["umbral"]["particion"],
        "Propagación de etiquetas": baselines["lpa"]["particion"],
    }
    modularity_options = {
        "Louvain": louvain["modularidad"],
        "Componentes por umbral": baselines["umbral"]["modularidad"],
        "Propagación de etiquetas": baselines["lpa"]["modularidad"],
    }
    partition = partition_options[algorithm_label]
    metrics = analyst.analizar_comunidades(analyzed_graph, partition)
    displayed_graph = analyzed_graph if graph_label == "Red analizada" else graph
    positions = graph_positions(graph)
    metrics_by_community = {item.id_comunidad: item for item in metrics}
    score_by_community = {
        community_id: item.puntaje_prioridad
        for community_id, item in metrics_by_community.items()
    }
    account_rows = []
    for node_id, node in displayed_graph.nodes.items():
        community_id = partition.get(node_id)
        account_rows.append({
            "Cuenta": node_id,
            "Tipo": node.tipo.replace("_", " ").capitalize(),
            "Grado": displayed_graph.grado(node_id),
            "Comunidad": f"C-{community_id}" if community_id is not None else "No evaluada",
            "Prioridad del grupo": score_by_community.get(community_id),
        })
    account_rows.sort(key=lambda row: row["Cuenta"])
    active_row = selected_row("community_accounts", account_rows)
    selected_node = str(active_row["Cuenta"]) if active_row else None
    community_color = {
        node_id: community_id
        for node_id, community_id in partition.items()
        if node_id in displayed_graph.nodes
    }
    modularity = modularity_options[algorithm_label]
    stability_text = (
        f"Estabilidad Louvain: **{louvain['estabilidad']:.0%}** · "
        if algorithm_label == "Louvain"
        else ""
    )
    st.markdown(
        f"**{displayed_graph.num_nodos} cuentas** · "
        f"**{displayed_graph.num_aristas} transferencias** · "
        f"Modularidad Q: **{modularity:.4f}** · "
        f"{stability_text}vista: {graph_label.lower()}"
    )

    graph_column, reading_column = st.columns([1.8, 1])
    with graph_column:
        st.header("Red de transacciones")
        st.plotly_chart(
            network_figure(
                displayed_graph,
                communities=community_color,
                selected_node=selected_node,
                measure=lambda edge: edge.monto,
                measure_label="Monto",
                edge_detail=lambda edge: f"Monto: {money(edge.monto)} · {edge.n_transferencias} transferencias",
                positions=positions,
                height=520,
            ),
            use_container_width=True,
            key=f"communities_network_{revision}",
            config={"displaylogo": False, "scrollZoom": True},
        )
    with reading_column:
        st.header("Lectura de la red")
        st.write(
            "Cada punto es una cuenta. El color agrupa la partición seleccionada; "
            "el grosor representa el monto. Pasa el cursor para ver cada enlace."
        )
        st.caption(
            f"El preprocesamiento dejó {analyzed_graph.num_nodos} cuentas y "
            f"{analyzed_graph.num_aristas} transferencias."
        )
        if analyst.nodos_excluidos:
            st.caption(
                f"Concentradores tratados: {len(analyst.nodos_excluidos)} "
                f"({hub_action_label.lower()})."
            )
        community_rows = [
            {
                "Comunidad": f"C-{item.id_comunidad}",
                "Cuentas": item.tamano,
                "Densidad": item.densidad_interna,
                "Volumen": item.volumen_total,
                "Prioridad de revisión": item.puntaje_prioridad,
            }
            for item in metrics
        ]
        st.dataframe(
            pd.DataFrame(community_rows),
            hide_index=True,
            use_container_width=True,
            height=260,
            column_config={
                "Volumen": st.column_config.NumberColumn(format="$ %.0f"),
                "Densidad": st.column_config.NumberColumn(format="%.2f"),
                "Prioridad de revisión": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    st.header("Cuentas del grafo")
    st.caption("Selecciona una fila para resaltar la cuenta en el diagrama.")
    format_table(account_rows, key="community_accounts")

    st.header("Comparación de particiones")
    st.plotly_chart(
        comparison_figure(
            ["Louvain", f"Umbral ({threshold:g})", "Propagación de etiquetas"],
            [
                louvain["modularidad"],
                baselines["umbral"]["modularidad"],
                baselines["lpa"]["modularidad"],
            ],
            title="Modularidad por algoritmo",
            value_label="Modularidad Q",
            colors=[GREEN, "#A07945", "#557D9C"],
        ),
        use_container_width=True,
        key=f"communities_comparison_{revision}",
        config={"displaylogo": False},
    )


def run_backbone() -> None:
    with st.sidebar:
        with st.form(key="backbone_form"):
            st.subheader("Vista")
            algorithm_label = st.selectbox("Árbol visible", ("Kruskal", "Prim"))
            with st.expander("Parámetros de optimización"):
                horizon = st.slider("Horizonte operativo (meses)", 1, 60, 12)
                alpha = st.slider("Peso del costo (α)", 0.1, 3.0, 1.0, 0.1)
                beta = st.slider("Peso de latencia (β)", 0.0, 5.0, 0.0, 0.1)
            submitted = st.form_submit_button(
                "Actualizar resultados",
                type="primary",
                use_container_width=True,
            )

    pending_params = {
        "algorithm_label": algorithm_label,
        "horizon": horizon,
        "alpha": alpha,
        "beta": beta,
    }
    params, revision = render_module_header(
        "backbone",
        "Red troncal de menor costo",
        "Datos sintéticos · Kruskal + Union-Find frente a Prim",
        pending_params,
        submitted,
    )
    algorithm_label = params["algorithm_label"]
    horizon = params["horizon"]
    alpha = params["alpha"]
    beta = params["beta"]

    try:
        graph = load_graph(BACKBONE_DATA)
    except (OSError, ValueError, ErrorRedFinanciera) as error:
        show_data_error(error)
        return

    optimizer = OptimizadorRedTroncal(
        horizonte_meses=float(horizon),
        alpha_costo=float(alpha),
        beta_latencia=float(beta),
    )
    kruskal = optimizer.ejecutar_kruskal(graph)
    prim = optimizer.ejecutar_prim(graph)
    result = kruskal if algorithm_label == "Kruskal" else prim
    fragility = optimizer.analizar_fragilidad(graph, result)
    savings = optimizer.calcular_ahorro_economico(graph, result)
    tree_edges = [(edge.origen, edge.destino) for edge in result.aristas_mst]

    st.markdown(
        f"**{graph.num_nodos} nodos** · **{graph.num_aristas} enlaces candidatos** · "
        f"Red completa: **{money(savings['costo_red_completa'])}** · "
        f"Red troncal: **{money(savings['costo_red_troncal'])}** · "
        f"Ahorro: **{money(savings['ahorro_absoluto'])} ({savings['porcentaje_ahorro']:.1f}%)**"
    )
    graph_column, reading_column = st.columns([1.8, 1])
    edge_rows = []
    for edge in graph.iter_aristas():
        cost = optimizer.funcion_costo(edge)
        in_tree = any(
            {edge.origen, edge.destino} == {u, v}
            for u, v in tree_edges
        )
        edge_rows.append({
            "Origen": edge.origen,
            "Destino": edge.destino,
            "Costo de instalación": edge.costo_instalacion,
            "Costo operativo / mes": edge.costo_operativo,
            "Latencia (ms)": edge.tiempo,
            "Costo ponderado": cost,
            "En red troncal": "Sí" if in_tree else "No",
            "_costo": cost,
        })
    edge_rows.sort(key=lambda row: (row["Origen"], row["Destino"]))
    active_row = selected_row("backbone_edges", edge_rows)

    with graph_column:
        st.header(f"Enlaces seleccionados por {algorithm_label}")
        st.plotly_chart(
            network_figure(
                graph,
                highlighted_edges=tree_edges,
                selected_edges=selected_pair(active_row),
                measure=optimizer.funcion_costo,
                measure_label="Costo ponderado",
                edge_detail=lambda edge: (
                    f"Costo ponderado: {money(optimizer.funcion_costo(edge))} · "
                    f"Latencia: {edge.tiempo:.1f} ms"
                ),
                height=520,
            ),
            use_container_width=True,
            key=f"backbone_network_{revision}",
            config={"displaylogo": False, "scrollZoom": True},
        )
    with reading_column:
        st.header("Estructura de la red")
        st.write(
            "Los enlaces verdes forman el árbol de expansión mínimo. "
            "Los demás son alternativas candidatas."
        )
        st.caption(
            f"{len(result.aristas_mst)} enlaces seleccionados · "
            f"{result.num_componentes} componentes conexas."
        )
        st.markdown(
            f"**Puntos de articulación:** {fragility['total_articulaciones']}  \n"
            f"**Puentes críticos:** {fragility['total_puentes']}"
        )
        if fragility["puntos_articulacion"]:
            st.caption(", ".join(fragility["puntos_articulacion"]))

    st.header("Enlaces candidatos")
    st.caption("Selecciona una fila para resaltar ese enlace en la red.")
    display_rows = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in edge_rows
    ]
    format_table(display_rows, key="backbone_edges")

    savings_chart = go.Figure(
        go.Bar(
            x=["Red completa", "Red troncal"],
            y=[savings["costo_red_completa"], savings["costo_red_troncal"]],
            marker_color=["#A98967", GREEN],
            hovertemplate="%{x}<br>Costo: $%{y:,.0f}<extra></extra>",
        )
    )
    savings_chart.update_layout(
        title={"text": "Costo total de infraestructura", "font": {"size": 16, "color": INK}},
        height=300,
        margin={"l": 12, "r": 12, "t": 48, "b": 14},
        paper_bgcolor=GROUND,
        plot_bgcolor=GROUND,
        showlegend=False,
        yaxis={"title": "USD", "showgrid": True, "gridcolor": "#DCD9CF"},
        xaxis={"showgrid": False},
        font={"color": INK, "family": "Arial, sans-serif", "size": 12},
    )
    st.plotly_chart(
        savings_chart,
        use_container_width=True,
        key=f"backbone_savings_{revision}",
        config={"displaylogo": False},
    )


def run_liquidity() -> None:
    with st.sidebar:
        with st.form(key="liquidity_form"):
            st.subheader("Vista")
            view_label = st.selectbox("Red", ("Red completa", "Rutas críticas"))
            with st.expander("Sensibilidad"):
                delta = st.slider(
                    "Aumento de capacidad por ruta",
                    10000,
                    200000,
                    50000,
                    10000,
                    format="$%d",
                )
            submitted = st.form_submit_button(
                "Actualizar resultados",
                type="primary",
                use_container_width=True,
            )

    pending_params = {
        "view_label": view_label,
        "delta": delta,
    }
    params, revision = render_module_header(
        "liquidity",
        "Distribución de liquidez",
        "Datos sintéticos · Dinic · verificación de flujo máximo y corte mínimo",
        pending_params,
        submitted,
    )
    view_label = params["view_label"]
    delta = params["delta"]

    try:
        graph = load_graph(LIQUIDITY_DATA)
        dataset = load_dataset(LIQUIDITY_DATA)
    except (OSError, ValueError, ErrorRedFinanciera, json.JSONDecodeError) as error:
        show_data_error(error)
        return

    supply = dataset.get("disponibilidad_bovedas", {})
    demand = dataset.get("demanda_agencias", {})
    if not isinstance(supply, dict) or not isinstance(demand, dict):
        show_data_error(ValueError("Faltan los datos de oferta de bóvedas o demanda de agencias."))
        return

    planner = PlanificadorDistribucionLiquidez(delta_sensibilidad=float(delta))
    with st.spinner("Calculando flujo máximo y corte mínimo..."):
        dinic = planner.optimizar_flujo_dinic(graph, supply, demand)
        edmonds_karp = planner.optimizar_flujo_edmonds_karp(graph, supply, demand)
        ford_fulkerson = planner.optimizar_flujo_ford_fulkerson(graph, supply, demand)
        sensitivity = planner.analizar_sensibilidad_cuellos_botella(
            graph,
            supply,
            demand,
            dinic,
        )
    augmented_graph = planner.preparar_red_con_supernodos(graph, supply, demand)
    total_supply = sum(supply.values())
    total_demand = sum(demand.values())
    deficit = max(0.0, total_demand - dinic.flujo_maximo)
    cut_edges = list(dinic.cuellos_de_botella)
    algorithm_comparison = [
        ("Dinic", dinic.flujo_maximo),
        ("Edmonds-Karp", edmonds_karp.flujo_maximo),
        ("Ford-Fulkerson", ford_fulkerson.flujo_maximo),
    ]

    cut_verified = abs(dinic.flujo_maximo - dinic.capacidad_corte) < 1e-4
    validation_text = "Verificado" if cut_verified else "Revisar resultado"
    st.markdown(
        f"**Flujo máximo:** {money(dinic.flujo_maximo)} · "
        f"Corte mínimo: **{money(dinic.capacidad_corte)} ({validation_text})** · "
        f"Déficit: **{money(deficit)}**"
    )
    st.caption(
        f"Oferta total {money(total_supply)} · Demanda total {money(total_demand)} · "
        f"{augmented_graph.num_nodos} nodos con superorigen y supersumidero."
    )

    edge_rows = []
    for edge in augmented_graph.iter_aristas():
        pair = (edge.origen, edge.destino)
        flow = dinic.flujo_aristas.get(pair, 0.0)
        is_cut = pair in cut_edges
        is_saturated = pair in dinic.aristas_saturadas
        status = (
            "Cuello de botella (corte mínimo)" if is_cut else
            "Saturada" if is_saturated else
            "Con capacidad disponible"
        )
        edge_rows.append({
            "Origen": edge.origen,
            "Destino": edge.destino,
            "Capacidad": edge.capacidad,
            "Flujo": flow,
            "Estado": status,
        })
    edge_rows.sort(key=lambda row: (row["Origen"], row["Destino"]))
    visible_edge_rows = (
        [row for row in edge_rows if (row["Origen"], row["Destino"]) in cut_edges]
        if view_label == "Rutas críticas"
        else edge_rows
    )
    table_key = "liquidity_critical_edges" if view_label == "Rutas críticas" else "liquidity_edges"
    active_row = selected_row(table_key, visible_edge_rows)
    selected_links = selected_pair(active_row)
    display_names = {
        ID_SUPER_FUENTE: "Origen de fondos",
        ID_SUPER_SUMIDERO: "Demanda total",
    }
    flow_values = dinic.flujo_aristas

    figure_graph = augmented_graph
    if view_label == "Rutas críticas":
        critical_graph = Graph(dirigido=True, ponderado=True)
        critical_nodes = {node_id for edge in cut_edges for node_id in edge}
        for node_id in critical_nodes:
            if node_id in augmented_graph.nodes:
                node = augmented_graph.nodes[node_id]
                critical_graph.agregar_nodo(node)
        for edge in augmented_graph.iter_aristas():
            if (edge.origen, edge.destino) in cut_edges:
                critical_graph.agregar_arista(edge)
        figure_graph = critical_graph

    st.header("Rutas de distribución")
    st.caption(
        "El grosor refleja capacidad; el color arcilla identifica aristas del corte mínimo. "
        "Pasa el cursor para comparar capacidad y flujo."
    )
    st.plotly_chart(
        network_figure(
            figure_graph,
            highlighted_edges=cut_edges,
            selected_edges=selected_links,
            measure=lambda edge: edge.capacidad,
            measure_label="Capacidad",
            edge_detail=lambda edge: (
                f"Capacidad: {money(edge.capacidad)} · "
                f"Flujo: {money(flow_values.get((edge.origen, edge.destino), 0.0))}"
            ),
            positions=flow_positions(augmented_graph),
            display_labels=display_names,
            height=500,
        ),
        use_container_width=True,
        key=f"liquidity_network_{revision}",
        config={"displaylogo": False, "scrollZoom": True},
    )

    st.header("Rutas y capacidades")
    st.caption("Selecciona una fila para resaltar el enlace en la red.")
    if not visible_edge_rows:
        st.info("No se identificaron aristas para mostrar en esta vista.")
    else:
        format_table(visible_edge_rows, key=table_key)

    agency_rows = []
    for agency_id, requested in sorted(demand.items()):
        delivered = dinic.flujo_aristas.get((agency_id, ID_SUPER_SUMIDERO), 0.0)
        agency_rows.append({
            "Agencia": agency_id,
            "Demanda": requested,
            "Recibido": delivered,
            "Déficit": max(0.0, requested - delivered),
        })
    agency_figure = go.Figure()
    agency_figure.add_trace(
        go.Bar(
            name="Demanda",
            x=[row["Agencia"] for row in agency_rows],
            y=[row["Demanda"] for row in agency_rows],
            marker_color="#A98967",
            hovertemplate="%{x}<br>Demanda: $%{y:,.0f}<extra></extra>",
        )
    )
    agency_figure.add_trace(
        go.Bar(
            name="Recibido",
            x=[row["Agencia"] for row in agency_rows],
            y=[row["Recibido"] for row in agency_rows],
            marker_color=GREEN,
            hovertemplate="%{x}<br>Recibido: $%{y:,.0f}<extra></extra>",
        )
    )
    agency_figure.update_layout(
        title={"text": "Demanda y efectivo recibido", "font": {"size": 16, "color": INK}},
        height=350,
        barmode="group",
        margin={"l": 12, "r": 12, "t": 48, "b": 14},
        paper_bgcolor=GROUND,
        plot_bgcolor=GROUND,
        legend={"orientation": "h", "y": 1.12, "x": 0},
        yaxis={"title": "USD", "showgrid": True, "gridcolor": "#DCD9CF"},
        xaxis={"showgrid": False},
        font={"color": INK, "family": "Arial, sans-serif", "size": 11},
    )
    st.plotly_chart(
        agency_figure,
        use_container_width=True,
        key=f"liquidity_agency_{revision}",
        config={"displaylogo": False},
    )

    st.header("Comprobación de algoritmos")
    st.plotly_chart(
        comparison_figure(
            [label for label, _ in algorithm_comparison],
            [value for _, value in algorithm_comparison],
            title="Flujo máximo calculado",
            value_label="Flujo (USD)",
            colors=[GREEN, "#557D9C", "#A07945"],
            decimals=0,
        ),
        use_container_width=True,
        key=f"liquidity_comparison_{revision}",
        config={"displaylogo": False},
    )
    st.caption(
        f"Conservación de flujo: {'válida' if dinic.conservacion_valida else 'revisar'} · "
        f"Capacidades respetadas: {'sí' if dinic.capacidades_respetadas else 'no'}."
    )

    if sensitivity:
        st.header("Sensibilidad de cuellos de botella")
        st.dataframe(
            pd.DataFrame([
                {
                    "Ruta": f"{item.origen} → {item.destino}",
                    "Capacidad actual": item.capacidad_actual,
                    "Ganancia marginal": item.ganancia_marginal,
                    "Eficiencia": item.eficiencia_inversion,
                }
                for item in sensitivity
            ]),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Capacidad actual": st.column_config.NumberColumn(format="$ %.0f"),
                "Ganancia marginal": st.column_config.NumberColumn(format="$ %.0f"),
                "Eficiencia": st.column_config.NumberColumn(format="%.2f"),
            },
        )


st.set_page_config(
    page_title="OptiFin · Redes financieras",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.header("OptiFin")
    st.caption("Teoría de grafos aplicada a finanzas")
    selected_module = st.radio("Explorar módulo", MODULES, label_visibility="visible")
    st.divider()
    st.caption("Demostración académica · conjuntos sintéticos")

if selected_module == "Comunidades":
    run_communities()
elif selected_module == "Red troncal":
    run_backbone()
else:
    run_liquidity()
