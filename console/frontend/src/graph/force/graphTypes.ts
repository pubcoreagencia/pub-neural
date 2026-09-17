import type { GraphNodeDTO } from "../../api/types";

export interface ForceNodeObject extends GraphNodeDTO {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  degree?: number;
  isCenter?: boolean;
  isSelected?: boolean;
  isHovered?: boolean;
  isNeighbor?: boolean;
  isDimmed?: boolean;
}

export interface ForceLinkObject {
  id: string;
  source: string | ForceNodeObject;
  target: string | ForceNodeObject;
  relation_type: string;
  weight: number;
  is_bidirectional: boolean;
  trust_zone: string;
  is_active: boolean;
  association_status?: "CONFIRMED" | "PROPOSED" | "UNCLASSIFIED" | string | null;
  classification_source?: string | null;
  classification_confidence?: number | null;
  classification_reason?: string | null;
  isSelected?: boolean;
  isHovered?: boolean;
  isDimmed?: boolean;
}

export interface GraphFilterCriteria {
  searchQuery: string;
  entityTypes: string[];
  relationTypes: string[];
  projectScope: string;
  trustZone: string;
  epistemicState: "ALL" | "CONFIRMED" | "PROPOSED";
}

export const ENTITY_COLORS: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  DECISION: { bg: "#1f1b2e", border: "#8b5cf6", text: "#e9d5ff", badge: "#4c1d95" },
  RULE: { bg: "#2a1e12", border: "#f59e0b", text: "#fef3c7", badge: "#78350f" },
  PATTERN: { bg: "#112629", border: "#06b6d4", text: "#cffafe", badge: "#164e63" },
  LESSON: { bg: "#13271d", border: "#10b981", text: "#d1fae5", badge: "#064e3b" },
  HOLDING: { bg: "#2d1b4e", border: "#a855f7", text: "#f3e8ff", badge: "#6b21a8" },
  PROJECT: { bg: "#142136", border: "#3b82f6", text: "#dbeafe", badge: "#1e3a8a" },
  REPOSITORY: { bg: "#1b212b", border: "#64748b", text: "#e2e8f0", badge: "#334155" },
  EVIDENCE: { bg: "#122333", border: "#0284c7", text: "#e0f2fe", badge: "#075985" },
  SOURCE: { bg: "#1e2229", border: "#6b7280", text: "#f3f4f6", badge: "#374151" },
  EVENT: { bg: "#2a151b", border: "#e11d48", text: "#ffe4e6", badge: "#881337" },
  DOCUMENT: { bg: "#282313", border: "#eab308", text: "#fef9c3", badge: "#713f12" },
  SKILL: { bg: "#28152e", border: "#d946ef", text: "#fae8ff", badge: "#701a75" },
  AGENT: { bg: "#291522", border: "#ec4899", text: "#fce7f3", badge: "#831843" },
  CONCEPT: { bg: "#221933", border: "#a855f7", text: "#f3e8ff", badge: "#581c87" },
};

export const DEFAULT_ENTITY_THEME = { bg: "#1a1f26", border: "#94a3b8", text: "#f1f5f9", badge: "#334155" };
