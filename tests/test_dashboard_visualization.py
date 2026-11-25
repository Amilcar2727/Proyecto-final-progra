from src.dashboard_visualization import CLAY, GREEN, network_figure
from src.graph import Edge, Graph, Node


def test_network_figure_highlights_selected_undirected_edge_and_node():
    graph = Graph(dirigido=False)
    graph.agregar_nodo(Node("A"))
    graph.agregar_nodo(Node("B"))
    graph.agregar_arista(Edge("A", "B", monto=250.0))

    figure = network_figure(
        graph,
        highlighted_edges=[("A", "B")],
        selected_edges=[("B", "A")],
        selected_node="B",
        measure=lambda edge: edge.monto,
        positions={"A": (-1.0, 0.0), "B": (1.0, 0.0)},
    )

    edge_traces = [trace for trace in figure.data if trace.name == "Enlace"]
    node_trace = next(trace for trace in figure.data if trace.name == "Nodos")

    assert len(edge_traces) == 1
    assert edge_traces[0].line.color == CLAY
    assert list(node_trace.marker.line.color) == ["#F8F6EF", CLAY]
    assert graph.num_nodos == 2
    assert graph.num_aristas == 1


def test_network_figure_uses_highlight_color_for_unselected_edge():
    graph = Graph(dirigido=False)
    graph.agregar_arista(Edge("A", "B", monto=100.0))

    figure = network_figure(graph, highlighted_edges=[("B", "A")])
    edge_trace = next(trace for trace in figure.data if trace.name == "Enlace")

    assert edge_trace.line.color == GREEN


def test_network_figure_explains_empty_graph():
    figure = network_figure(Graph())

    assert figure.layout.annotations[0].text == "No hay nodos para mostrar."
