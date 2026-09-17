import { useEffect, useState, useMemo } from "react";
import { NeuralAPI } from "../api/client";
import type {
  OverviewResponseDTO,
  OverviewProjectDTO,
  CandidateReviewDTO,
} from "../api/types";

interface OverviewViewProps {
  onSelectProjectForGraph?: (projectId: string) => void;
  onSelectProjectForTimeline?: (projectId: string) => void;
  onSelectEntityForGraph?: (entityId: string) => void;
  onUnauthorized?: () => void;
}

type FilterStatus = "TODOS" | "ATIVOS" | "EM_DESENVOLVIMENTO" | "ARQUIVADOS" | "SEM_OBSERVACOES";

export function OverviewView({
  onSelectProjectForGraph,
  onSelectProjectForTimeline,
  onSelectEntityForGraph,
  onUnauthorized,
}: OverviewViewProps) {
  const [data, setData] = useState<OverviewResponseDTO | null>(null);
  const [candidates, setCandidates] = useState<CandidateReviewDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [windowDays, setWindowDays] = useState(14);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("TODOS");
  const [filterCategory, setFilterCategory] = useState<string>("TODAS");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchOverview = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      NeuralAPI.getOverview(windowDays),
      NeuralAPI.getGovernanceReview().catch(() => ({ candidates: [] })),
    ])
      .then(([overviewRes, govRes]) => {
        setData(overviewRes);
        setCandidates(govRes.candidates || []);
      })
      .catch((err: any) => {
        const msg = err.message || "Falha ao carregar dados da visão geral";
        setError(msg);
        if (err.status === 401 || msg.includes("401")) {
          onUnauthorized?.();
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchOverview();
  }, [windowDays]);

  // Extract categories for filter
  const categories = useMemo(() => {
    if (!data?.projects) return [];
    const set = new Set<string>();
    data.projects.forEach((p) => {
      if (p.category) set.add(p.category);
    });
    return Array.from(set).sort();
  }, [data?.projects]);

  // Filtered projects
  const filteredProjects = useMemo(() => {
    if (!data?.projects) return [];
    return data.projects.filter((p) => {
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = (p.display_name || p.project_id).toLowerCase().includes(q);
        const matchId = p.project_id.toLowerCase().includes(q);
        const matchDesc = (p.description || "").toLowerCase().includes(q);
        if (!matchName && !matchId && !matchDesc) return false;
      }

      // Status filter
      if (filterStatus === "ATIVOS") {
        if (!p.is_active || p.is_archived) return false;
      } else if (filterStatus === "ARQUIVADOS") {
        if (!p.is_archived) return false;
      } else if (filterStatus === "SEM_OBSERVACOES") {
        if (p.observation_count > 0) return false;
      } else if (filterStatus === "EM_DESENVOLVIMENTO") {
        if (p.is_archived || p.observation_count === 0) return false;
      }

      // Category filter
      if (filterCategory !== "TODAS") {
        if (p.category !== filterCategory) return false;
      }

      return true;
    });
  }, [data?.projects, filterStatus, filterCategory, searchQuery]);

  if (loading && !data) {
    return (
      <div style={{ padding: "32px", color: "#94a3b8", fontFamily: "monospace" }}>
        Carregando Cockpit Operacional PUB Neural...
      </div>
    );
  }

  if (error && !data) {
    const isAuthError = error.includes("401");
    return (
      <div style={{ padding: "32px", color: "#f87171", fontFamily: "monospace" }}>
        Erro ao carregar Visão Geral: {error}
        <div style={{ marginTop: "16px", display: "flex", gap: "10px" }}>
          {isAuthError && onUnauthorized && (
            <button
              onClick={onUnauthorized}
              style={{
                padding: "8px 16px",
                background: "#0284c7",
                border: "none",
                color: "#ffffff",
                borderRadius: "4px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              🔐 Autenticar Sessão
            </button>
          )}
          <button
            onClick={fetchOverview}
            style={{
              padding: "8px 16px",
              background: "#1e293b",
              border: "1px solid #334155",
              color: "#f1f5f9",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  // Calendar days for activity heatmap
  const calendarDays: string[] = [];
  if (data?.daily_activity) {
    for (const item of data.daily_activity) {
      if (!calendarDays.includes(item.day)) {
        calendarDays.push(item.day);
      }
    }
  }
  calendarDays.sort();

  const getDailyCount = (day: string, projectId: string): number => {
    const found = data?.daily_activity.find(
      (d) => d.day === day && d.project_id === projectId
    );
    return found ? found.observed_count : 0;
  };

  const getIntensityColor = (count: number): string => {
    if (count === 0) return "#1e293b";
    if (count < 3) return "#0e7490";
    if (count < 10) return "#0284c7";
    if (count < 25) return "#2563eb";
    return "#3b82f6";
  };

  const exec = data?.executive_summary;

  return (
    <div
      style={{
        padding: "24px",
        overflowY: "auto",
        height: "100%",
        boxSizing: "border-box",
        backgroundColor: "#0b1120",
        color: "#f8fafc",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Header controls & System/Projector Health */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
          borderBottom: "1px solid #1e293b",
          paddingBottom: "16px",
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: "18px",
              fontWeight: 700,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              color: "#38bdf8",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>PUB NEURAL COMMAND CENTER</span>
            <span
              style={{
                fontSize: "10px",
                padding: "2px 6px",
                borderRadius: "4px",
                background: "#0369a1",
                color: "#e0f2fe",
              }}
            >
              COCKPIT EXECUTIVO
            </span>
          </h1>
          <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px" }}>
            Cockpit operacional da PUB Core Holding: registro canônico de projetos, repositórios monitorados e governança neural
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {/* Global System & Projector Health Badges */}
          <div style={{ display: "flex", gap: "8px" }}>
            <div
              style={{
                fontSize: "11px",
                padding: "4px 8px",
                borderRadius: "4px",
                backgroundColor:
                  data?.database_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.15)"
                    : "rgba(239, 68, 68, 0.15)",
                color: data?.database_health === "HEALTHY" ? "#34d399" : "#f87171",
                border: `1px solid ${
                  data?.database_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.3)"
                    : "rgba(239, 68, 68, 0.3)"
                }`,
                fontFamily: "monospace",
              }}
            >
              Banco de Dados: {data?.database_health === "HEALTHY" ? "SAUDÁVEL" : data?.database_health || "DESCONHECIDO"}
            </div>

            <div
              style={{
                fontSize: "11px",
                padding: "4px 8px",
                borderRadius: "4px",
                backgroundColor:
                  data?.projector_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.15)"
                    : data?.projector_health === "DEGRADED"
                    ? "rgba(245, 158, 11, 0.15)"
                    : "rgba(239, 68, 68, 0.15)",
                color:
                  data?.projector_health === "HEALTHY"
                    ? "#34d399"
                    : data?.projector_health === "DEGRADED"
                    ? "#fcd34d"
                    : "#f87171",
                border: `1px solid ${
                  data?.projector_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.3)"
                    : data?.projector_health === "DEGRADED"
                    ? "rgba(245, 158, 11, 0.3)"
                    : "rgba(239, 68, 68, 0.3)"
                }`,
                fontFamily: "monospace",
              }}
            >
              Projetores: {data?.projector_health === "HEALTHY" ? "SAUDÁVEL" : data?.projector_health === "DEGRADED" ? "DEGRADADO" : data?.projector_health || "DESCONHECIDO"}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>Janela:</span>
            <select
              value={windowDays}
              onChange={(e) => setWindowDays(Number(e.target.value))}
              style={{
                backgroundColor: "#1e293b",
                color: "#f8fafc",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "4px 8px",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              <option value={7}>7 Dias</option>
              <option value={14}>14 Dias</option>
              <option value={30}>30 Dias</option>
            </select>
            <button
              onClick={fetchOverview}
              style={{
                backgroundColor: "#1e293b",
                color: "#94a3b8",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "4px 10px",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* SECTION: RESUMO EXECUTIVO DA PUB CORE HOLDING */}
      {exec && (
        <div style={{ marginBottom: "28px" }}>
          <div
            style={{
              fontSize: "13px",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "#38bdf8",
              marginBottom: "12px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>Panorama Executivo da Holding</span>
            <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
              • Universo de projetos pubcoreagencia e atividade neural factual
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
              gap: "12px",
            }}
          >
            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Total de Projetos</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#f8fafc", marginTop: "4px" }}>{exec.total_projects}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Registrados no catálogo</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Projetos Ativos</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#34d399", marginTop: "4px" }}>{exec.active_projects}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Em operação / ciclo ativo</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Repositórios Monitorados</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#38bdf8", marginTop: "4px" }}>{exec.monitored_repositories}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Com monitoramento ativo</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Observações (7d)</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#60a5fa", marginTop: "4px" }}>{exec.recent_observations_7d}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Telemetria de repositório</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Eventos Hoje (UTC)</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#c084fc", marginTop: "4px" }}>{exec.events_today}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Eventos de fluxo registrados</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Conhecimentos Candidatos</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#f59e0b", marginTop: "4px" }}>{exec.candidate_knowledge_count}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Aguardando governança</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Conhecimentos Adotados</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#10b981", marginTop: "4px" }}>{exec.adopted_knowledge_count}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Validados soberanamente</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Saúde Neural</div>
              <div style={{ fontSize: "20px", fontWeight: 800, color: exec.neural_health === "SAUDAVEL" ? "#34d399" : "#fcd34d", marginTop: "6px" }}>
                {exec.neural_health === "SAUDAVEL" ? "SAUDÁVEL" : "DEGRADADO"}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Estado da infraestrutura</div>
            </div>
          </div>
        </div>
      )}

      {/* SECTION 0: CONHECIMENTO CANDIDATO AGUARDANDO GOVERNANÇA */}
      <div style={{ marginBottom: "32px" }}>
        <div
          style={{
            fontSize: "13px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#f59e0b",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>Conhecimento Candidato Aguardando Governança ({candidates.length})</span>
          <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
            • achados empíricos que exigem revisão soberana antes da promoção
          </span>
        </div>

        {candidates.length === 0 ? (
          <div
            style={{
              padding: "16px 20px",
              backgroundColor: "#0f172a",
              borderRadius: "6px",
              border: "1px dashed #334155",
              color: "#64748b",
              fontSize: "13px",
            }}
          >
            Nenhum nó de conhecimento candidato aguardando revisão de governança.
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
              gap: "16px",
            }}
          >
            {candidates.map((cand) => (
              <div
                key={cand.id}
                style={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #334155",
                  borderLeft: "3px solid #f59e0b",
                  borderRadius: "6px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
                  <span
                    style={{
                      fontSize: "10px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      backgroundColor: "rgba(245, 158, 11, 0.15)",
                      color: "#fbbf24",
                      fontFamily: "monospace",
                      fontWeight: 600,
                    }}
                  >
                    {cand.entity_type} • CANDIDATO
                  </span>
                  <span
                    style={{
                      fontSize: "11px",
                      color: "#94a3b8",
                      fontFamily: "monospace",
                    }}
                  >
                    {cand.project_id || "global"}
                  </span>
                </div>

                <div
                  style={{
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#f8fafc",
                    lineHeight: 1.4,
                  }}
                >
                  {cand.title}
                </div>

                {cand.summary && (
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#94a3b8",
                      lineHeight: 1.5,
                      maxHeight: "60px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {cand.summary}
                  </div>
                )}

                <div
                  style={{
                    fontSize: "11px",
                    color: "#64748b",
                    fontFamily: "monospace",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    borderTop: "1px solid #1e293b",
                    paddingTop: "8px",
                  }}
                >
                  <div>Proposto por: {cand.proposed_by_actor_id || "desconhecido"} ({cand.proposed_by_actor_role || "AGENT"})</div>
                  <div>Estado de Conflito: {cand.conflict_state}</div>
                  {cand.derived_from_experience_id && (
                    <div style={{ wordBreak: "break-all" }}>
                      Derivado de: {cand.derived_from_experience_id}
                    </div>
                  )}
                </div>

                {onSelectEntityForGraph && (
                  <div style={{ marginTop: "4px" }}>
                    <button
                      onClick={() => onSelectEntityForGraph(cand.id)}
                      style={{
                        padding: "4px 8px",
                        backgroundColor: "#1e293b",
                        border: "1px solid #334155",
                        color: "#38bdf8",
                        borderRadius: "4px",
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      Inspecionar no Grafo →
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 1: PROJETOS DA HOLDING (CATÁLOGO CANÔNICO & ATIVIDADE) */}
      <div style={{ marginBottom: "32px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
            marginBottom: "16px",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "13px",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                color: "#94a3b8",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>Projetos da PUB Core Holding ({filteredProjects.length} de {data?.projects.length || 0})</span>
              <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
                • Registro canônico, fontes factuais de observações e nós de conhecimento
              </span>
            </div>
          </div>

          {/* Filtros e Busca */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            {/* Input de Busca */}
            <input
              type="text"
              placeholder="Buscar projeto..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: "6px 10px",
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: "#f8fafc",
                fontSize: "12px",
                outline: "none",
                width: "160px",
              }}
            />

            {/* Filtro de Categoria */}
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              style={{
                padding: "6px 10px",
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: "#f8fafc",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              <option value="TODAS">Todas Categorias</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            {/* Filtros de Status */}
            <div
              style={{
                display: "flex",
                backgroundColor: "#1e293b",
                borderRadius: 4,
                padding: 2,
                border: "1px solid #334155",
              }}
            >
              {(["TODOS", "ATIVOS", "EM_DESENVOLVIMENTO", "ARQUIVADOS", "SEM_OBSERVACOES"] as FilterStatus[]).map((st) => {
                const labels: Record<FilterStatus, string> = {
                  TODOS: "Todos",
                  ATIVOS: "Ativos",
                  EM_DESENVOLVIMENTO: "Com Atividade",
                  ARQUIVADOS: "Arquivados",
                  SEM_OBSERVACOES: "Sem Obs.",
                };
                return (
                  <button
                    key={st}
                    onClick={() => setFilterStatus(st)}
                    style={{
                      padding: "4px 8px",
                      borderRadius: 3,
                      border: "none",
                      fontSize: "11px",
                      cursor: "pointer",
                      backgroundColor: filterStatus === st ? "#0284c7" : "transparent",
                      color: filterStatus === st ? "#ffffff" : "#94a3b8",
                      transition: "all 0.1s ease",
                    }}
                  >
                    {labels[st]}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {filteredProjects.length === 0 ? (
          <div
            style={{
              padding: "24px",
              backgroundColor: "#0f172a",
              borderRadius: "6px",
              border: "1px dashed #334155",
              color: "#64748b",
              fontSize: "13px",
            }}
          >
            Nenhum projeto encontrado para os filtros selecionados.
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
              gap: "16px",
            }}
          >
            {filteredProjects.map((proj: OverviewProjectDTO) => {
              const stateBadgeConfig = (() => {
                if (proj.is_archived || proj.project_state === "ARQUIVADO") {
                  return { label: "Arquivado", color: "#94a3b8", bg: "rgba(100, 116, 139, 0.15)", border: "rgba(100, 116, 139, 0.3)" };
                }
                if (proj.observation_count > 0 || proj.project_state === "ATIVO_OBSERVADO") {
                  return { label: "Ativo", color: "#34d399", bg: "rgba(16, 185, 129, 0.15)", border: "rgba(16, 185, 129, 0.3)" };
                }
                return { label: "Sem observações registradas", color: "#60a5fa", bg: "rgba(59, 130, 246, 0.1)", border: "rgba(59, 130, 246, 0.25)" };
              })();

              return (
                <div
                  key={proj.project_id}
                  style={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    padding: "16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          fontSize: "15px",
                          fontWeight: 700,
                          color: "#f1f5f9",
                        }}
                      >
                        {proj.display_name || proj.project_id}
                      </div>
                      <div style={{ fontSize: "11px", color: "#64748b", fontFamily: "monospace", marginTop: "2px" }}>
                        {proj.project_id}
                      </div>
                      {proj.description && (
                        <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px", lineHeight: "1.3", maxHeight: "32px", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {proj.description}
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
                      {proj.category && (
                        <span
                          style={{
                            fontSize: "9px",
                            padding: "2px 6px",
                            borderRadius: "3px",
                            backgroundColor: "#1e293b",
                            color: "#38bdf8",
                            fontWeight: 600,
                            fontFamily: "monospace",
                          }}
                        >
                          {proj.category}
                        </span>
                      )}
                      <div
                        style={{
                          fontSize: "11px",
                          color: "#94a3b8",
                          fontFamily: "monospace",
                        }}
                      >
                        Nós Ativos: <strong style={{ color: "#38bdf8" }}>{proj.active_node_count}</strong>
                      </div>
                    </div>
                  </div>

                  {/* Metrics Grid */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr 1fr",
                      gap: "8px",
                      backgroundColor: "#1e293b",
                      padding: "10px",
                      borderRadius: "6px",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase" }}>
                        Hoje (UTC)
                      </div>
                      <div style={{ fontSize: "16px", fontWeight: 700, color: "#38bdf8" }}>
                        {proj.activity_today}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase" }}>
                        7 Dias (UTC)
                      </div>
                      <div style={{ fontSize: "16px", fontWeight: 700, color: "#e2e8f0" }}>
                        {proj.activity_7d}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase" }}>
                        Total Obs.
                      </div>
                      <div style={{ fontSize: "16px", fontWeight: 700, color: "#cbd5e1" }}>
                        {proj.observation_count}
                      </div>
                    </div>
                  </div>

                  {/* Estado e Indicadores de Governança */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "8px",
                      fontSize: "11px",
                      fontFamily: "monospace",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ color: "#64748b" }}>ESTADO:</span>
                      <span
                        style={{
                          padding: "2px 6px",
                          borderRadius: "3px",
                          backgroundColor: stateBadgeConfig.bg,
                          color: stateBadgeConfig.color,
                          border: `1px solid ${stateBadgeConfig.border}`,
                          fontSize: "10px",
                          fontWeight: 600,
                        }}
                      >
                        {stateBadgeConfig.label}
                      </span>
                    </div>

                    {proj.blocked_nodes_count > 0 ? (
                      <span
                        style={{
                          padding: "2px 6px",
                          borderRadius: "3px",
                          backgroundColor: "rgba(239, 68, 68, 0.15)",
                          color: "#f87171",
                          border: "1px solid rgba(239, 68, 68, 0.3)",
                        }}
                      >
                        Nós Bloqueados: {proj.blocked_nodes_count}
                      </span>
                    ) : (
                      <span style={{ color: "#475569" }}>Nós Bloqueados: 0</span>
                    )}
                  </div>

                  {/* Latest Operational Signal Section */}
                  <div
                    style={{
                      backgroundColor: "#090d16",
                      border: "1px solid #1e293b",
                      borderRadius: "6px",
                      padding: "8px 10px",
                      fontSize: "11px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "9px",
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                          color: "#64748b",
                          fontWeight: 600,
                        }}
                      >
                        ÚLTIMO SINAL OPERACIONAL
                      </span>
                      {proj.latest_signal ? (
                        <span
                          style={{
                            fontSize: "9px",
                            padding: "1px 5px",
                            borderRadius: "3px",
                            backgroundColor:
                              proj.latest_signal.type === "TASK_EXPERIENCE_RECORDED"
                                ? "rgba(16, 185, 129, 0.15)"
                                : "rgba(59, 130, 246, 0.15)",
                            color:
                              proj.latest_signal.type === "TASK_EXPERIENCE_RECORDED"
                                ? "#34d399"
                                : "#60a5fa",
                            fontFamily: "monospace",
                          }}
                        >
                          {proj.latest_signal.type === "TASK_EXPERIENCE_RECORDED"
                            ? "SINAL DE TAREFA"
                            : "TELEMETRIA"}
                        </span>
                      ) : null}
                    </div>

                    {proj.latest_signal ? (
                      <>
                        <div
                          style={{
                            color: "#f1f5f9",
                            fontWeight: 500,
                            lineHeight: "1.3",
                            wordBreak: "break-word",
                          }}
                        >
                          {proj.latest_signal.summary}
                        </div>
                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            justifyContent: "space-between",
                            color: "#64748b",
                            fontSize: "10px",
                            marginTop: "2px",
                            gap: "4px",
                          }}
                        >
                          <span>
                            {proj.latest_signal.timestamp
                              ? new Date(proj.latest_signal.timestamp).toUTCString().slice(0, 22)
                              : ""}
                          </span>
                          <span
                            title={`Origem: ${proj.latest_signal.source} | Localizador: ${proj.latest_signal.locator}`}
                            style={{
                              fontFamily: "monospace",
                              color: "#94a3b8",
                              maxWidth: "180px",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {proj.latest_signal.locator}
                          </span>
                        </div>
                      </>
                    ) : (
                      <div style={{ color: "#475569", fontStyle: "italic" }}>
                        Nenhum sinal operacional registrado
                      </div>
                    )}
                  </div>

                  {/* Secondary Meta: Last Observed & GitHub */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: "11px",
                      color: "#64748b",
                    }}
                  >
                    <span>
                      Última Obs:{" "}
                      {proj.last_observation_at
                        ? new Date(proj.last_observation_at).toUTCString().slice(0, 16)
                        : "Nenhuma"}
                    </span>
                    {proj.github_url && (
                      <a
                        href={proj.github_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: "#38bdf8", textDecoration: "none" }}
                      >
                        GitHub ↗
                      </a>
                    )}
                  </div>

                  {/* Ações de Detalhamento */}
                  <div
                    style={{
                      display: "flex",
                      gap: "8px",
                      marginTop: "4px",
                      paddingTop: "8px",
                      borderTop: "1px solid #1e293b",
                    }}
                  >
                    <button
                      onClick={() => onSelectProjectForGraph?.(proj.project_id)}
                      style={{
                        flex: 1,
                        backgroundColor: "#1e293b",
                        color: "#38bdf8",
                        border: "1px solid #334155",
                        borderRadius: "4px",
                        padding: "6px 8px",
                        fontSize: "11px",
                        cursor: "pointer",
                        fontWeight: 500,
                      }}
                    >
                      Ver no Grafo →
                    </button>
                    <button
                      onClick={() => onSelectProjectForTimeline?.(proj.project_id)}
                      style={{
                        flex: 1,
                        backgroundColor: "#1e293b",
                        color: "#94a3b8",
                        border: "1px solid #334155",
                        borderRadius: "4px",
                        padding: "6px 8px",
                        fontSize: "11px",
                        cursor: "pointer",
                        fontWeight: 500,
                      }}
                    >
                      Linha do Tempo →
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: MAPA DE CALOR DE ATIVIDADE DIÁRIA */}
      <div>
        <div
          style={{
            fontSize: "13px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#94a3b8",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>Atividade de Repositórios Observados ({data?.window_days || windowDays} Dias Calendário UTC)</span>
          <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
            • 0 indica ausência de novas observações registradas no intervalo (e não inatividade do projeto)
          </span>
        </div>

        {data?.projects.filter(p => p.observation_count > 0).length === 0 || calendarDays.length === 0 ? (
          <div
            style={{
              padding: "24px",
              backgroundColor: "#0f172a",
              borderRadius: "6px",
              border: "1px dashed #334155",
              color: "#64748b",
              fontSize: "13px",
            }}
          >
            Nenhuma atividade diária observada nesta janela temporal.
          </div>
        ) : (
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
              padding: "16px",
              overflowX: "auto",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "12px",
              }}
            >
              <thead>
                <tr>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "8px 12px",
                      borderBottom: "1px solid #1e293b",
                      color: "#94a3b8",
                      width: "180px",
                    }}
                  >
                    Projeto Observado
                  </th>
                  {calendarDays.map((day) => (
                    <th
                      key={day}
                      style={{
                        padding: "8px 6px",
                        borderBottom: "1px solid #1e293b",
                        color: "#64748b",
                        fontSize: "10px",
                        textAlign: "center",
                        fontFamily: "monospace",
                      }}
                    >
                      {day.slice(5)}
                    </th>
                  ))}
                  <th
                    style={{
                      textAlign: "right",
                      padding: "8px 12px",
                      borderBottom: "1px solid #1e293b",
                      color: "#94a3b8",
                      width: "80px",
                    }}
                  >
                    Soma Janela
                  </th>
                </tr>
              </thead>
              <tbody>
                {data?.projects
                  .filter((p) => p.observation_count > 0)
                  .map((proj) => {
                    let sum = 0;

                    return (
                      <tr key={proj.project_id}>
                        <td
                          style={{
                            padding: "8px 12px",
                            borderBottom: "1px solid #1e293b",
                            fontFamily: "monospace",
                            color: "#f1f5f9",
                          }}
                        >
                          {proj.display_name || proj.project_id}
                        </td>
                        {calendarDays.map((day) => {
                          const cnt = getDailyCount(day, proj.project_id);
                          sum += cnt;
                          return (
                            <td
                              key={day}
                              style={{
                                padding: "6px",
                                borderBottom: "1px solid #1e293b",
                                textAlign: "center",
                              }}
                            >
                              <div
                                title={`${proj.project_id} em ${day} (UTC): ${cnt} observações registradas`}
                                style={{
                                  width: "24px",
                                  height: "24px",
                                  margin: "0 auto",
                                  borderRadius: "3px",
                                  backgroundColor: getIntensityColor(cnt),
                                  color: cnt > 0 ? "#ffffff" : "#475569",
                                  fontSize: "10px",
                                  lineHeight: "24px",
                                  fontFamily: "monospace",
                                }}
                              >
                                {cnt > 0 ? cnt : "0"}
                              </div>
                            </td>
                          );
                        })}
                        <td
                          style={{
                            padding: "8px 12px",
                            borderBottom: "1px solid #1e293b",
                            textAlign: "right",
                            fontFamily: "monospace",
                            fontWeight: 600,
                            color: sum > 0 ? "#38bdf8" : "#64748b",
                          }}
                        >
                          {sum}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
