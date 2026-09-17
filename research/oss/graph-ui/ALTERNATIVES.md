# Graph Visualization Alternatives Evaluation

| Library | Rendering Technology | React Integration | Node Styling Flexibility | Built-in Layout | Performance Ceiling | Evaluation for PUB Neural Console |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **React Flow (`@xyflow/react`)** | **DOM (HTML) + SVG** | **Native React Components** | **Unlimited (Pure React / Tailwind)** | None (External: Dagre / D3) | ~1,000–2,000 nodes | **SELECTED FOR V0.** Optimal developer ergonomics, native React cards for entities. |
| **Cytoscape.js** | HTML5 Canvas / WebGL | Imperative wrapper via `ref` | Canvas shapes & stylesheets | Extensive built-in (Cola, CoSE, Dagre) | ~10,000–50,000 nodes | **ARCHITECTURAL BACKUP.** Superior for massive graphs, but loses native React DOM cards. |
| **Sigma.js** | WebGL | React wrapper (`react-sigma`) | WebGL shaders / canvas | External (`graphology`) | 100,000+ nodes | **NOT RECOMMENDED.** Designed for massive web graphs; poor fit for rich entity cards. |
| **vis-network** | HTML5 Canvas | Imperative wrapper | Canvas shapes / images | Built-in physics simulation | ~2,000–5,000 nodes | **NOT RECOMMENDED.** Legacy architecture, non-idiomatic React integration. |
