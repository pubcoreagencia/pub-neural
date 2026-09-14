# xyflow/xyflow — Architecture Analysis

## 1. Rendering Architecture (DOM + SVG Hybrid)
* **Nodes:** Rendered as standard HTML DOM elements wrapped in absolutely positioned containers. This enables embedding arbitrary React components, Tailwind styling, form inputs, badges, and buttons directly inside nodes.
* **Edges:** Rendered inside a shared SVG viewport layer using SVG `<path>` elements. Supports bezier, smooth step, straight, and custom paths.
* **Overlays:** Custom edge labels and interactive action buttons rendered via `EdgeLabelRenderer` (React Portals).

## 2. Built-in Features
* `<MiniMap />`: Scaled-down SVG overview with customizable node colors and interactive panning.
* `<Controls />`: Built-in zoom in/out, fit-to-view, and lock canvas buttons.
* `<Background />`: Canvas grid patterns (dots, lines, cross).
* Viewport handling: Programmatic pan and zoom via `useReactFlow()`, selection marquee, keyboard navigation, and accessibility (a11y) support.

## 3. Performance Profile
* Optimal range: 1 to 500 nodes (60 FPS with complex HTML cards).
* Moderate range: 500 to 2,000 nodes (requires `onlyRenderVisibleElements` viewport culling and `React.memo`).
* Large-scale networks (>5,000 nodes): DOM overhead becomes a bottleneck; WebGL-based engines (Sigma.js, Cytoscape Canvas) are required at massive scale.

## 4. Layout Engine Requirement
* **React Flow does NOT calculate node coordinates automatically.**
* Nodes must be supplied with explicit `{ x, y }` coordinates.
* External layout engines must be paired with React Flow:
  * **Dagre (`@dagrejs/dagre`):** Deterministic directed acyclic graphs and hierarchical trees.
  * **D3-Force (`d3-force`):** Physics-based force simulation for organic network clustering.
  * **ELK.js (`elkjs`):** Complex orthogonal and nested multi-tier layouts.
