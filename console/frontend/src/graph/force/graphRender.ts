import { ENTITY_COLORS, DEFAULT_ENTITY_THEME, type ForceNodeObject, type ForceLinkObject } from "./graphTypes";

/**
 * Calculates node radius based on connections (degree) and grounded evidence.
 */
export function getNodeRadius(node: ForceNodeObject): number {
  const entityType = node.entity_type?.toUpperCase();
  // ORGANIZATION is the holding root apex
  if (entityType === "ORGANIZATION" || entityType === "HOLDING") {
    return 24;
  }
  // PROJECT is the primary semantic architectural layer between ORG and REPOSITORIES
  if (entityType === "PROJECT") {
    const degree = node.degree || 1;
    return Math.min(Math.max(14 + Math.sqrt(degree) * 1.5, 15), 24);
  }

  const degree = node.degree || 1;
  const evidenceBonus = Math.min((node.evidence_count || 0) * 0.5, 4);
  const base = 5 + Math.sqrt(degree) * 2.2 + evidenceBonus;
  return Math.min(Math.max(base, 6), 28);
}

/**
 * Custom Canvas renderer for nodes supporting adaptive Level-of-Detail (LOD):
 * - ORGANIZATION / PROJECT: Always legible with title/badge even at zoom >= 0.35.
 * - Other entities:
 *   - LOD 0 (zoom < 0.9): Colored node dot with glowing halo on selection/hover.
 *   - LOD 1 (0.9 <= zoom < 1.8): Colored node + Entity Type badge.
 *   - LOD 2 (zoom >= 1.8): Colored node + Title label + promotion status.
 */
export function renderCanvasNode(
  node: ForceNodeObject,
  ctx: CanvasRenderingContext2D,
  globalScale: number
): void {
  const x = node.x ?? 0;
  const y = node.y ?? 0;
  const r = getNodeRadius(node);
  const entityType = node.entity_type?.toUpperCase();
  const theme = ENTITY_COLORS[entityType] || DEFAULT_ENTITY_THEME;

  const isSelected = !!node.isSelected;
  const isHovered = !!node.isHovered;
  const isNeighbor = !!node.isNeighbor;
  const isDimmed = !!node.isDimmed;
  const isProjectOrOrg = entityType === "ORGANIZATION" || entityType === "PROJECT" || entityType === "HOLDING";

  ctx.save();

  // Opacity
  ctx.globalAlpha = isDimmed ? 0.2 : 1.0;

  // Outer glow / halo on selected, hovered, center or high-level project/org nodes
  if (isSelected || isHovered || node.isCenter || isProjectOrOrg) {
    ctx.beginPath();
    ctx.arc(x, y, r + (isSelected ? 6 : isProjectOrOrg ? 3 : 2), 0, 2 * Math.PI, false);
    ctx.fillStyle = isSelected
      ? "rgba(56, 189, 248, 0.45)"
      : isProjectOrOrg
      ? "rgba(59, 130, 246, 0.18)"
      : "rgba(167, 139, 250, 0.3)";
    ctx.fill();
  }

  // Main Node Circle
  ctx.beginPath();
  ctx.arc(x, y, r, 0, 2 * Math.PI, false);
  ctx.fillStyle = theme.bg;
  ctx.fill();

  // Border ring
  ctx.lineWidth = isSelected ? 2.8 : isProjectOrOrg ? 2.2 : isNeighbor ? 2 : 1.5;
  ctx.strokeStyle = isSelected ? "#38bdf8" : isNeighbor ? "#38bdf8" : theme.border;
  ctx.stroke();

  // Draw Center Dot
  ctx.beginPath();
  ctx.arc(x, y, Math.max(r * 0.3, 2), 0, 2 * Math.PI, false);
  ctx.fillStyle = theme.border;
  ctx.fill();

  // Adaptive Typography Rendering
  if (!isDimmed) {
    // Structural nodes (ORGANIZATION & PROJECT) are visible early (globalScale >= 0.35)
    // or if hovered/selected so users immediately perceive the Project layer.
    if (isProjectOrOrg || globalScale >= 0.9 || isHovered || isSelected) {
      const showTitleEarly = isProjectOrOrg || globalScale >= 1.5 || isHovered || isSelected;

      // Type badge / label
      ctx.font = `600 ${Math.max(10 / globalScale, 3.5)}px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = theme.text;
      const typeLabel = node.entity_type.toUpperCase();
      ctx.fillText(typeLabel, x, y + r + 2);

      // Detailed Title & Promotion State
      if (showTitleEarly) {
        ctx.font = `500 ${Math.max(8.5 / globalScale, 3)}px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
        ctx.fillStyle = isProjectOrOrg ? "#93c5fd" : "#cbd5e1";
        const titleLabel = node.title.length > 26 ? `${node.title.slice(0, 24)}…` : node.title;
        ctx.fillText(titleLabel, x, y + r + (13 / globalScale) + 2);

        if (node.promotion_state) {
          ctx.font = `bold ${Math.max(7 / globalScale, 2.5)}px monospace`;
          ctx.fillStyle =
            node.promotion_state === "VALIDATED" || node.promotion_state === "INSTITUTIONAL"
              ? "#34d399"
              : "#fbbf24";
          ctx.fillText(`[${node.promotion_state}]`, x, y + r + (23 / globalScale) + 2);
        }
      }
    }
  }

  ctx.restore();
}

/**
 * Custom Canvas renderer for links:
 * - Solid for EXTRACTED / confirmed relations.
 * - Dashed for INFERRED relations.
 * - Glowing Red for CONTRADICTS relations.
 */
export function renderCanvasLink(
  link: ForceLinkObject,
  ctx: CanvasRenderingContext2D,
  globalScale: number
): void {
  const source = link.source as ForceNodeObject;
  const target = link.target as ForceNodeObject;
  if (!source || !target || source.x === undefined || target.x === undefined) return;

  const isSelected = !!link.isSelected;
  const isHovered = !!link.isHovered;
  const isDimmed = !!link.isDimmed;
  const isContradiction = link.relation_type === "CONTRADICTS";
  const isBridge = link.relation_type === "IMPLEMENTS" || link.relation_type === "VALIDATED_BY";
  const isProposed = link.epistemic_classification === "PROPOSED" || link.association_status === "PROPOSED";
  const isInferred = link.epistemic_classification === "INFERRED" || link.relation_type === "RELATED_TO";

  ctx.save();
  ctx.globalAlpha = isDimmed ? 0.15 : isSelected || isHovered ? 0.95 : isBridge ? 0.75 : 0.45;

  ctx.beginPath();
  ctx.moveTo(source.x, source.y!);
  ctx.lineTo(target.x, target.y!);

  if (isContradiction) {
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = (isSelected || isHovered ? 2.5 : 1.8) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([]);
  } else if (isProposed) {
    ctx.strokeStyle = isSelected || isHovered ? "#fbbf24" : "#b45309";
    ctx.lineWidth = (isSelected || isHovered ? 2.0 : 1.2) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([2 / globalScale, 3 / globalScale]);
  } else if (isInferred) {
    ctx.strokeStyle = isSelected || isHovered ? "#38bdf8" : "#94a3b8";
    ctx.lineWidth = (isSelected || isHovered ? 2.0 : 1.2) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([4 / globalScale, 4 / globalScale]);
  } else if (isBridge) {
    // Distinct cyan/emerald bridge styling for physical-cognitive connections
    ctx.strokeStyle = isSelected || isHovered ? "#38bdf8" : "#0ea5e9";
    ctx.lineWidth = (isSelected || isHovered ? 2.5 : 1.6) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([]);
  } else {
    ctx.strokeStyle = isSelected || isHovered ? "#38bdf8" : "#475569";
    ctx.lineWidth = (isSelected || isHovered ? 2.2 : 1.2) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([]);
  }

  ctx.stroke();
  ctx.restore();
}
