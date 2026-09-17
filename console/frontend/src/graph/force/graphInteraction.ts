import type { ForceNodeObject, ForceLinkObject } from "./graphTypes";

/**
 * Computes degree for each node and marks neighbor highlights on hover or selection.
 */
export function calculateDegreesAndHighlights(
  nodes: ForceNodeObject[],
  links: ForceLinkObject[],
  activeId: string | null
): { nodes: ForceNodeObject[]; links: ForceLinkObject[] } {
  // 1. Calculate degree for all nodes
  const degreeMap = new Map<string, number>();
  const neighborSet = new Set<string>();
  const connectedLinkIds = new Set<string>();

  links.forEach((link) => {
    const sId = typeof link.source === "object" ? link.source.id : link.source;
    const tId = typeof link.target === "object" ? link.target.id : link.target;

    degreeMap.set(sId, (degreeMap.get(sId) || 0) + 1);
    degreeMap.set(tId, (degreeMap.get(tId) || 0) + 1);

    if (activeId && (sId === activeId || tId === activeId)) {
      neighborSet.add(sId);
      neighborSet.add(tId);
      connectedLinkIds.add(link.id);
    }
  });

  // 2. Map nodes with highlight & degree state
  const updatedNodes = nodes.map((node) => {
    const deg = degreeMap.get(node.id) || 1;
    const isSelected = activeId === node.id;
    const isNeighbor = activeId ? neighborSet.has(node.id) : false;
    const isDimmed = activeId ? !isSelected && !isNeighbor : false;

    return {
      ...node,
      degree: deg,
      isSelected,
      isNeighbor,
      isDimmed,
    };
  });

  // 3. Map links with highlight state
  const updatedLinks = links.map((link) => {
    const isConnected = activeId ? connectedLinkIds.has(link.id) : false;
    const isDimmed = activeId ? !isConnected : false;

    return {
      ...link,
      isSelected: isConnected,
      isDimmed,
    };
  });

  return { nodes: updatedNodes, links: updatedLinks };
}
