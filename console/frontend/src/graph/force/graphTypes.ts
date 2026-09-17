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
  epistemic_classification?: "EXTRACTED" | "INFERRED" | "PROPOSED" | string | null;
  evidence_locator?: any;
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
  epistemicState: "ALL" | "EXTRACTED" | "INFERRED" | "PROPOSED" | "CONFIRMED";
}

export const ENTITY_COLORS: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  ORGANIZATION: { bg: "#2a163d", border: "#c084fc", text: "#f3e8ff", badge: "#7e22ce" },
  DECISION: { bg: "#1f1b2e", border: "#8b5cf6", text: "#e9d5ff", badge: "#4c1d95" },
  RULE: { bg: "#2a1e12", border: "#f59e0b", text: "#fef3c7", badge: "#78350f" },
  PATTERN: { bg: "#112629", border: "#06b6d4", text: "#cffafe", badge: "#164e63" },
  LESSON: { bg: "#13271d", border: "#10b981", text: "#d1fae5", badge: "#064e3b" },
  HOLDING: { bg: "#2d1b4e", border: "#a855f7", text: "#f3e8ff", badge: "#6b21a8" },
  PROJECT: { bg: "#142136", border: "#3b82f6", text: "#dbeafe", badge: "#1e3a8a" },
  REPOSITORY: { bg: "#16233b", border: "#0ea5e9", text: "#bae6fd", badge: "#0369a1" },
  EVIDENCE: { bg: "#122333", border: "#0284c7", text: "#e0f2fe", badge: "#075985" },
  SOURCE: { bg: "#1e293b", border: "#60a5fa", text: "#e2e8f0", badge: "#2563eb" },
  EVENT: { bg: "#2a151b", border: "#f43f5e", text: "#ffe4e6", badge: "#be123c" },
  DOCUMENT: { bg: "#1c2e24", border: "#34d399", text: "#d1fae5", badge: "#059669" },
  SKILL: { bg: "#28152e", border: "#d946ef", text: "#fae8ff", badge: "#701a75" },
  AGENT: { bg: "#291522", border: "#ec4899", text: "#fce7f3", badge: "#831843" },
  CONCEPT: { bg: "#2d2315", border: "#f59e0b", text: "#fef3c7", badge: "#b45309" },
};

export const DEFAULT_ENTITY_THEME = { bg: "#1a1f26", border: "#94a3b8", text: "#f1f5f9", badge: "#334155" };
