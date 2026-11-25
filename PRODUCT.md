# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: Streamlit and Plotly for a local Python-only visualization interface; the existing algorithms, graph model, and datasets remain the source of truth.

## Users

Students and the instructor for a one-time Programming III project, exploring financial-network graph algorithms and their results.

## Product Purpose

OptiFin models financial networks and demonstrates community detection, minimum-cost backbone design, and liquidity distribution. The interface should make the three existing scenarios and their graph-based results easier to explore and explain.

## Positioning

The project implements its graph algorithms from scratch in Python; NetworkX is reserved for visualization layouts and test oracles, not for solving the scenarios.

## Operating Context

Used locally as an academic project demonstration. Reproducible synthetic datasets are stored in `data/` and can be regenerated with `python scripts/generar_datos.py`.

## Capabilities and Constraints

- Preserve the existing graph model and algorithms for Louvain community detection, Kruskal/Union-Find, and Dinic/max-flow min-cut.
- Visualize all three existing scenarios and their synthetic datasets.
- Keep the interface and implementation in Python and Python libraries, running locally.
- Community findings are review indicators, not proof of fraud or money laundering.

## Evidence on Hand

- Existing implementation and tests under `src/` and `tests/`.
- Reproducible synthetic data in `data/transacciones.json`, `data/red_troncal.json`, and `data/distribucion_liquidez.json`.
- Existing command-line demonstrations and generated reports; no real financial data or production deployment is in scope.

## Product Principles

- Keep the existing algorithms as the source of analytical results.
- Make the graph structure and its scenario-specific metrics easy to understand.
- Clearly distinguish synthetic examples from real financial evidence.
- Present community analysis as an investigative aid, never as a fraud determination.
