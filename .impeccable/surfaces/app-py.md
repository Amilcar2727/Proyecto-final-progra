---
version: 1
slug: "app-py"
primary_target: "app.py"
related_targets: []
---

# OptiFin Explorer

## Scope and mode

Local Streamlit application for exploring the project's three existing financial-network scenarios. Operate surface; built code-first in Python.

## Surface brief

- **Audience and task:** Programming III students and instructor inspect the synthetic graphs, compare algorithm outputs, and explain how each result relates to the original network.
- **Action and evidence:** choose Communities, Backbone, or Liquidity; read the network diagram and scenario-specific metrics; change a supported algorithm or parameter; inspect the linked result table.
- **Content:** existing reproducible JSON datasets and results produced by the project's own algorithms.
- **Constraints:** Python and Python libraries only for the shipped interface; local use; no new frontend stack, real financial data, unsupported claims, or changes to algorithm implementations. NetworkX remains a visualization-layout aid, not a solver. Community groups are review indicators, not proof of wrongdoing.
- **Success:** students can identify the network, the algorithm's output, and its key measures without leaving the visualization.
- **Unresolved decisions:** none.

## Direction contract

**THESIS:** Treat each algorithm's input and output as comparable field plates: the student reads the graph first, then sees how the algorithm changes its interpretation. Refuse the default dashboard where metrics float free of the network they measure.

**OWN-WORLD:** Botanical atlas plates lend the screen a restrained paper ground, graphite labels, leaf-green structure, and a small clay-red signal. Standard app navigation and controls remain familiar. The signature is a registered network view: node positions and scale stay fixed while community, selected backbone, or minimum-cut states change; every visual encoding has a persistent legend.

**STORY:** Select one of three modules, inspect its synthetic network, then switch its supported algorithm or parameter and compare the resulting communities, minimum-cost links, or liquidity bottlenecks. Selecting an entity in the linked table identifies it in the graph. Clearly label synthetic data and keep community analysis non-accusatory.

**FIRST VIEWPORT:** A standard left navigation names Communities, Backbone, and Liquidity. The Communities view opens with its title and synthetic-data status, then a compact line of modularity and stability results. One large interactive transaction graph carries the main weight; its stable layout, community colors, selected account, and legend explain the analysis. A concise linked table and comparison measures sit directly below the graph, not in detached metric cards.

**FORM:** Botanical field-plate system, candidate 5 of 7 in the grounded direction list; chosen direction. seed:54bf0faf1c15d748.

**FINISH:** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
