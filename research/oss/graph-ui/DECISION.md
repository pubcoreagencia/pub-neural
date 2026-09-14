# Architectural Decision: xyflow/xyflow (React Flow)

## Final Decision
```text
DECISION: ADOPT — presentation layer (CODE ADOPTION for future frontend)
```

## Concrete Rationale
1. **Perfect Scope Alignment:** React Flow is purely a front-end rendering library. Adopting it incurs zero risk to backend databases, event sourcing, or governance.
2. **Component Ergonomics:** Custom nodes are standard React components, allowing rich Tailwind-styled cards with category badges, status indicators, and click handlers for `DECISION`, `RULE`, `PATTERN`, and `LESSON` entities.
3. **Batteries Included:** Provides `<Controls />`, `<MiniMap />`, pan/zoom interactions, and selection marquees out of the box.
4. **Layout Strategy:** Will be paired with `@dagrejs/dagre` for hierarchical lineage DAGs and `d3-force` for organic knowledge network views.
5. **Implementation Status:** `NOT IMPLEMENTED / FUTURE`. No code or dependencies will be added until the Console phase is officially authorized.
