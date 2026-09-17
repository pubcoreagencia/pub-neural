import { ENTITY_COLORS, DEFAULT_ENTITY_THEME, type ForceNodeObject, type ForceLinkObject } from "./graphTypes";

/**
 * Calculates node radius based on connections (degree) and grounded evidence.
 */
export function getNodeRadius(node: ForceNodeObject): number {
  const degree = node.degree || 1;
  const evidenceBonus = Math.min((node.evidence_count || 0) * 0.5, 4);
  const base = 5 + Math.sqrt(degree) * 2.2 + evidenceBonus;
  return Math.min(Math.max(base, 6), 28);
}

/**
 * Custom Canvas renderer for nodes supporting 3 Level-of-Detail (LOD) modes:
 * - LOD 0 (zoom < 1.2): Colored node dot with glowing halo on selection.
 * - LOD 1 (1.2 <= zoom < 2.5): Colored node + Entity Type badge.
 * - LOD 2 (zoom >= 2.5): Colored node + Title label + promotion status.
 */
export function renderCanvasNode(
  node: ForceNodeObject,
  ctx: CanvasRenderingContext2D,
  globalScale: number
): void {
  const x = node.x ?? 0;
  const y = node.y ?? 0;
  const r = getNodeRadius(node);
  const theme = ENTITY_COLORS[node.entity_type?.toUpperCase()] || DEFAULT_ENTITY_THEME;

  const isSelected = !!node.isSelected;
  const isHovered = !!node.isHovered;
  const isNeighbor = !!node.isNeighbor;
  const isDimmed = !!node.isDimmed;

  ctx.save();

  // Opacity
  ctx.globalAlpha = isDimmed ? 0.2 : 1.0;

  // Outer glow / halo on selected, hovered or center nodes
  if (isSelected || isHovered || node.isCenter) {
    ctx.beginPath();
    ctx.arc(x, y, r + (isSelected ? 5 : 3), 0, 2 * Math.PI, false);
    ctx.fillStyle = isSelected ? "rgba(56, 189, 248, 0.4)" : "rgba(167, 139, 250, 0.3)";
    ctx.fill();
  }

  // Main Node Circle
  ctx.beginPath();
  ctx.arc(x, y, r, 0, 2 * Math.PI, false);
  ctx.fillStyle = theme.bg;
  ctx.fill();

  // Border ring
  ctx.lineWidth = isSelected ? 2.5 : isNeighbor ? 2 : 1.5;
  ctx.strokeStyle = isSelected ? "#38bdf8" : isNeighbor ? "#38bdf8" : theme.border;
  ctx.stroke();

  // Draw Center Dot
  ctx.beginPath();
  ctx.arc(x, y, Math.max(r * 0.3, 2), 0, 2 * Math.PI, false);
  ctx.fillStyle = theme.border;
  ctx.fill();

  // Level of Detail (LOD) Typography Rendering
  if (!isDimmed) {
    if (globalScale >= 1.2 || isHovered || isSelected) {
      ctx.font = `600 ${Math.max(10 / globalScale, 3.5)}px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";

      // LOD 1: Type label
      ctx.fillStyle = theme.text;
      const typeLabel = node.entity_type.toUpperCase();
      ctx.fillText(typeLabel, x, y + r + 2);

      // LOD 2: Detailed Title & Promotion State
      if (globalScale >= 2.0 || isHovered || isSelected) {
        ctx.font = `500 ${Math.max(8.5 / globalScale, 3)}px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
        ctx.fillStyle = "#cbd5e1";
        const titleLabel = node.title.length > 24 ? `${node.title.slice(0, 22)}…` : node.title;
        ctx.fillText(titleLabel, x, y + r + (14 / globalScale) + 2);

        if (node.promotion_state) {
          ctx.font = `bold ${Math.max(7 / globalScale, 2.5)}px monospace`;
          ctx.fillStyle = node.promotion_state === "VALIDATED" || node.promotion_state === "INSTITUTIONAL" ? "#34d399" : "#fbbf24";
          ctx.fillText(`[${node.promotion_state}]`, x, y + r + (25 / globalScale) + 2);
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
  const isInferred = link.association_status === "PROPOSED" || link.relation_type === "RELATED_TO";

  ctx.save();
  ctx.globalAlpha = isDimmed ? 0.15 : isSelected || isHovered ? 0.95 : 0.45;

  ctx.beginPath();
  ctx.moveTo(source.x, source.y!);
  ctx.lineTo(target.x, target.y!);

  if (isContradiction) {
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = (isSelected || isHovered ? 2.5 : 1.8) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([]);
  } else if (isInferred) {
    ctx.strokeStyle = isSelected || isHovered ? "#38bdf8" : "#94a3b8";
    ctx.lineWidth = (isSelected || isHovered ? 2.0 : 1.2) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([4 / globalScale, 4 / globalScale]);
  } else {
    ctx.strokeStyle = isSelected || isHovered ? "#38bdf8" : "#475569";
    ctx.lineWidth = (isSelected || isHovered ? 2.2 : 1.2) / Math.max(globalScale * 0.8, 1);
    ctx.setLineDash([]);
  }

  ctx.stroke();
  ctx.restore();
}
