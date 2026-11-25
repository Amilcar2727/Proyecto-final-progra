---
name: OptiFin
description: Botanical field plates for comparing financial-network algorithms
world: botanical-folio
colors:
  paper-ground: "#F8F6EF"
  atlas-paper: "#F3EFE3"
  atlas-secondary: "#E9E4D5"
  graphite: "#26332D"
  streamlit-text: "#000F08"
  muted-graphite: "#657168"
  leaf-green: "#477653"
  clay-red: "#C75B3B"
  edge-gray: "#9AA69B"
  grid-gray: "#DCD9CF"
  warm-taupe: "#A07945"
  blue-violet: "#557D9C"
  dried-rose: "#855F68"
typography:
  display:
    fontFamily: "sans-serif"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.33
spacing:
  compact: "8px"
  medium: "12px"
  panel: "14px"
  section: "22px"
---

# Design System: OptiFin

## Overview

**Creative North Star: "The Botanical Field Plate"**

OptiFin presents financial-network algorithms as restrained, comparable scientific plates. Paper-like surfaces carry graphite text, leaf-green structure, and a small clay-red signal for selection or bottlenecks. The interface stays native to Streamlit: the app uses familiar navigation and controls rather than recreating dashboard furniture.

The main visual priority is the registered network. Its node positions remain stable across supported states, graph scale stays comparable within a view, and persistent legends explain community or node-type encoding. Tables sit with the graph or directly below it as part of the analysis, not as detached decoration.

**Key Characteristics:**
- Paper ground with graphite and muted green labels
- Leaf-green as the primary analytical structure
- Clay red reserved for active or critical state
- Stable, interactive network positions
- Standard Streamlit density and controls

## Colors

The palette is paper-and-ink with two functional accents. Botanical greens carry normal structure and selected positive outputs; clay red identifies selection or minimum-cut state.

### Primary
- **Leaf Green** (#477653): default analysis structure, selected backbone edges, received values, and the Streamlit primary control color.
- **Clay Red** (#C75B3B): selected nodes or edges and minimum-cut / critical routes. It is a small, purposeful signal rather than a dominant surface.

### Secondary
- **Atlas Taupe** (#A07945): a community comparison series and warm node/category cue.
- **Dried Blue** (#557D9C): a community comparison series and blue-toned node/category cue.
- **Dried Rose** (#855F68): a node-type category cue.

### Tertiary
- **Veil Gray** (#9AA69B): neutral, unselected graph edges.
- **Grid Gray** (#DCD9CF): chart grid lines and rules.

### Neutral
- **Graphite** (#26332D): Plotly text, titles, hover labels, and graph labels.
- **Streamlit Ink** (#000F08): application text configured in Streamlit.
- **Plate Ground** (#F8F6EF): Plotly graph canvas and figure ground.
- **Atlas Paper** (#F3EFE3): Streamlit page background.
- **Atlas Secondary** (#E9E4D5): Streamlit secondary surface.
- **Muted Graphite** (#657168): subdued graph text and fallback node color.

**The Restrained Signal Rule.** Clay red, selected borders, and critical edges communicate state; they do not replace labels or legends.

## Typography

**Display Font:** Streamlit sans serif
**Body Font:** Streamlit sans serif
**Label/Mono Font:** Arial, sans-serif for Plotly labels and chart text

The shipped interface uses a familiar sans-serif reading voice. Plotly and comparison charts explicitly use Arial at 11–12px for data labels, while Streamlit supplies the main title, body, and control typography.

### Hierarchy
- **Display** (sans serif, 32px, bold, 1.2 line-height): Streamlit page titles such as module names.
- **Title** (sans serif, 16px, bold): Plotly chart and section titles.
- **Body** (sans serif, 16px, 400, 1.45 line-height): app copy, captions, and linked analysis prose.
- **Label** (Arial, 11–12px, 400): Plotly legends, hover text, tick labels, and table-adjacent chart context.

**The Units Stay Visible Rule.** Financial figures use explicit `$`, USD captions, and 0–3 decimal precision appropriate to modularity or flow rather than relying on abbreviated numeric treatment.

## Layout

The app uses a standard collapsed-left Streamlit sidebar for module navigation and scenario controls. Page content is wide, with graph-led desktop regions split approximately 1.8:1 between the network plate and its linked reading column. Graph heights are scenario-specific and stable: 520px for communities and backbone, 500px for liquidity.

Tables and comparison charts follow their source graph rather than floating in independent metric cards. Streamlit columns, headers, captions, and full-width controls maintain a compact academic reading rhythm. The `.streamlit/config.toml` base layout is wide and the sidebar starts collapsed.

## Elevation & Depth

The system is flat by default. Depth comes from paper/secondary paper separation, thin chart rules, edge weight, node size, and explicit selection borders rather than shadows or raised cards.

**The Flat-By-Default Rule.** Use no ambient shadow on the dashboard. Graph nodes use a paper border to separate them from the plot ground and a clay outline for selection.

## Shapes

The observed form language is restrained and mostly rectilinear: Streamlit controls and tables, Plotly charts, thin warm-gray plot rules, and full-width data regions. Graph nodes are circular and vary in size with degree. No project-specific radius scale or established corner-family was found in the implementation.

**The Direct Geometry Rule.** Preserve circular nodes, horizontal legends, and thin borders. Do not introduce cards, ornamental containers, or hard offset shadows.

## Components

### Navigation
- **Style:** Standard Streamlit sidebar with OptiFin heading, module radio, divider, and synthetic-data caption.
- **Active State:** The selected radio row is the active module; no custom active rail or icon treatment is implemented.
- **Language:** Module names remain “Comunidades,” “Red troncal,” and “Distribución de liquidez.”

### Inputs / Controls
- **Style:** Standard Streamlit selectboxes, sliders, expander groups, and radio controls. The sidebar owns scenario controls.
- **States:** Use native Streamlit interaction states and labels; do not restyle controls outside Python/Streamlit primitives.

### Linked Tables
- **Style:** Full-width pandas-backed `st.dataframe`, no visible index, single-row selection, and a fixed usable height.
- **Behavior:** Selecting an account or edge reruns the page and highlights the matching graph entity. Scenarios use 330px account/edge table heights where applicable.
- **Language:** Selection captions name the action before the table.

### Network Plates
- **Canvas:** Plate Ground (#F8F6EF), 520px or 500px tall, no visible axes, pan mode, and scroll zoom.
- **Edges:** Edge Gray default, Leaf Green highlighted, Clay Red selected. Width scales with the measured value.
- **Nodes:** Circular, Leaf Green or typed-community color, paper outline by default, 3px Clay Red outline for selection.
- **Legends:** Horizontal, bottom-aligned, persistent, 11px Graphite text.

### Algorithm Comparisons
- **Style:** Horizontal or grouped Plotly bars on Plate Ground, with Graphite titles and Grid Gray grid lines.
- **Assignment:** Leaf Green is the primary/default result; Taupe and Dried Blue separate comparator bars or series.
- **Labels:** Values and units appear explicitly without Plotly's toolbar.

## Do's and Don'ts

### Do:
- **Do** keep node positions stable by supplying the same graph layout seed or explicit layer positions.
- **Do** pair graph state with text and a persistent legend.
- **Do** label every analytical dataset as synthetic.
- **Do** keep community results as review indicators, never accusations or determinations.
- **Do** use standard Streamlit controls and Python/Plotly implementations.
- **Do** place result tables beside or immediately below the graph they explain.

### Don't:
- **Don't** float summary metrics as detached decorative cards.
- **Don't** replace graph colors with color alone; supply labels, captions, legends, or table text.
- **Don't** use hard offset shadows or a dark app shell.
- **Don't** introduce a new frontend stack or custom icon glyph system.
- **Don't** canonize the mock's botanical eyebrow or decorative kicker treatments; they are not shipped by the application.
