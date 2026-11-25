"""
Pruebas unitarias y de integración para el Módulo 5 (Evaluación y Benchmarks).
"""

from src.evaluacion_resultados import (
    EvaluadorResultados,
    calcular_metricas_clasificacion_pares,
    estimar_pendiente_log_log,
)


def test_metricas_clasificacion_pares():
    real = {"A": 0, "B": 0, "C": 1, "D": 1}
    # Predicción perfecta
    pred_perfecta = {"A": 5, "B": 5, "C": 8, "D": 8}
    m_perf = calcular_metricas_clasificacion_pares(pred_perfecta, real)
    assert m_perf["precision"] == 1.0
    assert m_perf["recall"] == 1.0
    assert m_perf["f1"] == 1.0

    # Predicción donde todo se junta en 1 sola comunidad (Recall 1.0, pero baja precisión por falsos positivos)
    pred_junta = {"A": 0, "B": 0, "C": 0, "D": 0}
    m_junta = calcular_metricas_clasificacion_pares(pred_junta, real)
    assert m_junta["recall"] == 1.0
    assert m_junta["precision"] < 1.0


def test_estimacion_pendiente_log_log():
    tamanos = [100, 200, 400, 800]
    # Simular O(N^2)
    tiempos = [0.01 * (n ** 2) for n in tamanos]
    pendiente = estimar_pendiente_log_log(tamanos, tiempos)
    assert abs(pendiente - 2.0) < 0.05


def test_benchmark_mst_kruskal_y_prim():
    evaluador = EvaluadorResultados(seed=42)
    registros = evaluador.benchmark_mst(tamanos=[20, 50], repeticiones=2, densidad="dispersa")

    assert len(registros) == 4
    # Comprobar que en cada tamaño Kruskal y Prim obtienen el mismo peso
    kruskal_20 = next(r for r in registros if r.algoritmo == "Kruskal" and r.nodos_v == 20)
    prim_20 = next(r for r in registros if r.algoritmo == "Prim" and r.nodos_v == 20)
    assert kruskal_20.metrica_calidad == prim_20.metrica_calidad
    assert kruskal_20.tiempo_medio_seg > 0.0
    assert kruskal_20.memoria_pico_kb > 0.0


def test_benchmark_flujo_dinic_y_ek():
    evaluador = EvaluadorResultados(seed=42)
    registros = evaluador.benchmark_flujo(tamanos=[15, 30], repeticiones=1)

    dinic_reg = [r for r in registros if r.algoritmo == "Dinic"]
    ek_reg = [r for r in registros if r.algoritmo == "Edmonds-Karp"]
    assert len(dinic_reg) == 2
    assert len(ek_reg) == 2
    # Deben coincidir en el flujo máximo calculado
    assert dinic_reg[0].metrica_calidad == ek_reg[0].metrica_calidad


def test_casos_dificiles_adversarios():
    evaluador = EvaluadorResultados(seed=42)
    res_dificiles = evaluador.validar_casos_dificiles_comunidades()

    assert "caso_a_concentrador" in res_dificiles
    assert "caso_b_mulas_debiles" in res_dificiles
    assert "caso_c_puente_fuerte" in res_dificiles

    # Caso B: Louvain detecta las mulas mientras que el umbral alto las pierde
    assert res_dificiles["caso_b_mulas_debiles"]["louvain_agrupa"] is True
    assert res_dificiles["caso_b_mulas_debiles"]["umbral_alto_pierde_mulas"] is True
