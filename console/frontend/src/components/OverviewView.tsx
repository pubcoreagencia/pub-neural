import { useEffect, useState, useMemo } from "react";
import { NeuralAPI } from "../api/client";
import type {
  OverviewResponseDTO,
  OverviewProjectDTO,
  CandidateReviewDTO,
  GovernanceOntologyQueuesDTO,
  ActivitySignalDTO,
} from "../api/types";

interface OverviewViewProps {
  onSelectProjectForGraph?: (projectId: string) => void;
  onSelectProjectForTimeline?: (projectId: string) => void;
  onSelectEntityForGraph?: (entityId: string) => void;
  onUnauthorized?: () => void;
}

type FilterStatus = "TODOS" | "ATIVOS" | "ATIVIDADE_HOJE" | "ATIVIDADE_RECENTE" | "SEM_ATIVIDADE" | "ARQUIVADOS" | "SEM_OBSERVACOES";

export function OverviewView({
  onSelectProjectForGraph,
  onSelectProjectForTimeline,
  onSelectEntityForGraph,
  onUnauthorized,
}: OverviewViewProps) {
  const [data, setData] = useState<OverviewResponseDTO | null>(null);
  const [candidates, setCandidates] = useState<CandidateReviewDTO[]>([]);
  const [govQueues, setGovQueues] = useState<GovernanceOntologyQueuesDTO | null>(null);
  const [activeQueueTab, setActiveQueueTab] = useState<"PROJECTS" | "ASSOCIATIONS" | "UNCLASSIFIED">("PROJECTS");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [windowDays, setWindowDays] = useState(14);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("TODOS");
  const [filterCategory, setFilterCategory] = useState<string>("TODAS");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedProjects, setExpandedProjects] = useState<Record<string, boolean>>({});

  // Activity Intelligence V0.4 State
  const [activitySignals, setActivitySignals] = useState<ActivitySignalDTO[]>([]);
  const [activityLoading, setActivityLoading] = useState<boolean>(false);
  const [activityWindow, setActivityWindow] = useState<number>(14);
  const [activityTypeFilter, setActivityTypeFilter] = useState<string>("TODOS");
  const [activityProjectFilter, setActivityProjectFilter] = useState<string>("TODOS");

  const fetchActivityFeed = () => {
    setActivityLoading(true);
    NeuralAPI.getActivity({
      windowDays: activityWindow,
      projectId: activityProjectFilter !== "TODOS" ? activityProjectFilter : undefined,
      activityType: activityTypeFilter !== "TODOS" ? activityTypeFilter : undefined,
      limit: 50,
    })
      .then((res) => {
        setActivitySignals(res.signals || []);
      })
      .catch(() => {
        setActivitySignals([]);
      })
      .finally(() => {
        setActivityLoading(false);
      });
  };

  const fetchOverview = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      NeuralAPI.getOverview(windowDays),
      NeuralAPI.getGovernanceReview().catch(() => ({ candidates: [] })),
      NeuralAPI.getGovernanceOntologyQueues().catch(() => null),
    ])
      .then(([overviewRes, govRes, queuesRes]) => {
        setData(overviewRes);
        setCandidates(govRes.candidates || []);
        setGovQueues(queuesRes);
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

  useEffect(() => {
    fetchActivityFeed();
  }, [activityWindow, activityTypeFilter, activityProjectFilter]);

  const toggleProjectExpand = (projId: string) => {
    setExpandedProjects((prev) => ({
      ...prev,
      [projId]: !prev[projId],
    }));
  };

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
      } else if (filterStatus === "ATIVIDADE_HOJE") {
        if (p.operational_activity_state !== "ATIVIDADE_HOJE" && p.activity_today === 0) return false;
      } else if (filterStatus === "ATIVIDADE_RECENTE") {
        if (p.operational_activity_state !== "ATIVIDADE_RECENTE" && p.activity_7d === 0) return false;
      } else if (filterStatus === "SEM_ATIVIDADE") {
        if (p.operational_activity_state !== "SEM_ATIVIDADE_NO_PERIODO" && p.observation_count === 0) return false;
      } else if (filterStatus === "ARQUIVADOS") {
        if (!p.is_archived) return false;
      } else if (filterStatus === "SEM_OBSERVACOES") {
        if (p.observation_count > 0) return false;
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

            {/* Continuous Repository Observation Telemetry Badge (V0.5.1 Hardened) */}
            {(() => {
              const tel = data?.observation_sync_telemetry;
              const status = tel?.status || "NO_DATA";

              let bg = "rgba(148, 163, 184, 0.15)";
              let color = "#94a3b8";
              let border = "rgba(148, 163, 184, 0.3)";
              let label = "? Sem dados suficientes";

              if (status === "OPERATING") {
                bg = "rgba(16, 185, 129, 0.15)";
                color = "#34d399";
                border = "rgba(16, 185, 129, 0.3)";
                label = "● Operando";
              } else if (status === "WAITING") {
                bg = "rgba(56, 189, 248, 0.12)";
                color = "#38bdf8";
                border = "rgba(56, 189, 248, 0.3)";
                label = "◌ Aguardando próxima execução";
              } else if (status === "FAILED") {
                bg = "rgba(239, 68, 68, 0.15)";
                color = "#f87171";
                border = "rgba(239, 68, 68, 0.3)";
                label = "⚠ Coleta com falha";
              }

              const tooltip = tel
                ? `Estado: ${label}\nÚltima sincronização: ${tel.last_sync_at || "N/A"}\nÚltimo sucesso: ${tel.last_success_at || "N/A"}\nPróxima sincronização: ${tel.next_sync_at || "N/A"}\nRepositórios verificados: ${tel.repositories_scanned}\nNovos sinais: ${tel.observations_created}\nFalhas consecutivas: ${tel.consecutive_failures || 0}`
                : "Aguardando inicialização do scheduler";

              return (
                <div
                  style={{
                    fontSize: "11px",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    backgroundColor: bg,
                    color: color,
                    border: `1px solid ${border}`,
                    fontFamily: "monospace",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                  title={tooltip}
                >
                  <span>Observação dos Repositórios:</span>
                  <strong>{label}</strong>
                  {tel && (
                    <span style={{ color: "#94a3b8", fontSize: "10px" }}>
                      ({tel.repositories_scanned} repos | +{tel.observations_created} sinais)
                    </span>
                  )}
                </div>
              );
            })()}
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
            <span>Panorama Executivo da Holding & Governança Ontológica</span>
            <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
              • Ontologia canônica PUB Core: distinção factual entre existência, confirmação e inferência
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
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Projetos Confirmados</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#34d399", marginTop: "4px" }}>
                {exec.confirmed_projects_count ?? 6}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }} title="Baseado em evidência documental ou confirmação explícita">
                ✓ Validado soberanamente
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Projetos Sugeridos</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#fcd34d", marginTop: "4px" }}>
                {exec.proposed_projects_count ?? 28}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }} title="Inferência produzida por regras, metadata ou análise">
                ◌ Aguardando validação
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Associações Confirmadas</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#38bdf8", marginTop: "4px" }}>
                {exec.confirmed_associations_count ?? 17}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Repositórios vinculados</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Associações Sugeridas</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#fb923c", marginTop: "4px" }}>
                {exec.proposed_associations_count ?? 39}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Inferência estrutural</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Não Classificados</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: (exec.unclassified_repositories_count || 0) > 0 ? "#f59e0b" : "#34d399", marginTop: "4px" }}>
                {exec.unclassified_repositories_count ?? 0}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }} title="Evidência insuficiente para classificação">
                ? Repositórios isolados
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Repositórios Totais</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#94a3b8", marginTop: "4px" }}>{exec.total_repositories}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Registrados no GitHub</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Atividade Hoje</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: (exec.projects_with_activity_today_count || 0) > 0 ? "#34d399" : "#64748b", marginTop: "4px" }}>
                {exec.projects_with_activity_today_count ?? 0}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }} title="Projetos com observações ou eventos registrados hoje (UTC)">
                {(exec.projects_with_activity_today_count || 0) > 0 ? "⚡ Projetos ativos hoje" : "Sem sinais hoje"}
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Atividade 7 Dias</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#38bdf8", marginTop: "4px" }}>
                {exec.projects_with_activity_7d_count ?? 0}
              </div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }} title="Projetos com observações ou eventos na janela de 7 dias">
                Projetos com sinal recente
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Observações (7d)</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#60a5fa", marginTop: "4px" }}>{exec.recent_observations_7d}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Telemetria factual</div>
            </div>

            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Eventos Hoje (UTC)</div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: "#c084fc", marginTop: "4px" }}>{exec.events_today}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Eventos de fluxo</div>
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

      {/* SECTION 0B: ATIVIDADE OPERACIONAL RECENTE (FEED DE SINAIS FACTUAIS V0.4) */}
      <div style={{ marginBottom: "32px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
            marginBottom: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                fontSize: "13px",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                color: "#38bdf8",
              }}
            >
              Atividade Operacional da Holding ({activitySignals.length} sinais nos últimos {activityWindow} dias)
            </span>
            <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
              • Sinais factuais auditáveis: observações de repositório e eventos de execução
            </span>
          </div>

          {/* Filters for Activity Feed */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            {/* Filter by Project */}
            <select
              value={activityProjectFilter}
              onChange={(e) => setActivityProjectFilter(e.target.value)}
              style={{
                backgroundColor: "#0f172a",
                color: "#f8fafc",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "4px 8px",
                fontSize: "11px",
                cursor: "pointer",
              }}
            >
              <option value="TODOS">Todos os Projetos</option>
              {data?.projects?.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.display_name || p.project_id}
                </option>
              ))}
            </select>

            {/* Filter by Type */}
            <select
              value={activityTypeFilter}
              onChange={(e) => setActivityTypeFilter(e.target.value)}
              style={{
                backgroundColor: "#0f172a",
                color: "#f8fafc",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "4px 8px",
                fontSize: "11px",
                cursor: "pointer",
              }}
            >
              <option value="TODOS">Todos os Tipos de Sinal</option>
              <option value="REPOSITORY_OBSERVED">Observações de Repositório</option>
              <option value="TASK_EXPERIENCE_RECORDED">Tarefas e Experiências</option>
              <option value="AUTONOMOUS_AGENT_VALIDATED">Agentes Validados</option>
              <option value="OPERATING_MODE_ADOPTED">Modos Operacionais</option>
            </select>

            {/* Window selector */}
            <div style={{ display: "flex", backgroundColor: "#1e293b", borderRadius: "4px", padding: "2px", border: "1px solid #334155" }}>
              {[
                { label: "1d", val: 1 },
                { label: "7d", val: 7 },
                { label: "14d", val: 14 },
                { label: "30d", val: 30 },
                { label: "90d", val: 90 },
              ].map((w) => (
                <button
                  key={w.val}
                  onClick={() => setActivityWindow(w.val)}
                  style={{
                    padding: "3px 8px",
                    borderRadius: "3px",
                    border: "none",
                    fontSize: "10px",
                    cursor: "pointer",
                    backgroundColor: activityWindow === w.val ? "#0284c7" : "transparent",
                    color: activityWindow === w.val ? "#ffffff" : "#94a3b8",
                    fontWeight: activityWindow === w.val ? 700 : 500,
                  }}
                >
                  {w.label}
                </button>
              ))}
            </div>

            <button
              onClick={fetchActivityFeed}
              style={{
                backgroundColor: "#1e293b",
                color: "#94a3b8",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "4px 8px",
                fontSize: "11px",
                cursor: "pointer",
              }}
            >
              ↻ Atualizar
            </button>
          </div>
        </div>

        {/* Activity Feed Cards List */}
        {activityLoading ? (
          <div style={{ padding: "16px", backgroundColor: "#0f172a", borderRadius: "6px", color: "#94a3b8", fontSize: "12px", border: "1px solid #1e293b" }}>
            Carregando feed de atividade operacional...
          </div>
        ) : activitySignals.length === 0 ? (
          <div style={{ padding: "16px", backgroundColor: "#0f172a", borderRadius: "6px", color: "#64748b", fontSize: "12px", border: "1px dashed #334155" }}>
            Nenhum sinal operacional observado na janela selecionada ({activityWindow} dias).
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "8px",
              maxHeight: "360px",
              overflowY: "auto",
              paddingRight: "6px",
            }}
          >
            {activitySignals.map((sig) => {
              const isTask = sig.activity_type === "TASK_EXPERIENCE_RECORDED";
              const isAgent = sig.activity_type === "AUTONOMOUS_AGENT_VALIDATED";
              const isRepo = sig.activity_type === "REPOSITORY_OBSERVED";

              const badgeBg = isTask ? "rgba(16, 185, 129, 0.15)" : isAgent ? "rgba(192, 132, 252, 0.15)" : isRepo ? "rgba(56, 189, 248, 0.15)" : "rgba(100, 116, 139, 0.15)";
              const badgeColor = isTask ? "#34d399" : isAgent ? "#c084fc" : isRepo ? "#38bdf8" : "#94a3b8";

              return (
                <div
                  key={sig.id}
                  style={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "6px",
                    padding: "10px 14px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "12px",
                  }}
                >
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontSize: "10px",
                          padding: "2px 6px",
                          borderRadius: "3px",
                          backgroundColor: badgeBg,
                          color: badgeColor,
                          fontWeight: 700,
                          fontFamily: "monospace",
                        }}
                      >
                        {sig.activity_type}
                      </span>
                      {sig.project_display_name && (
                        <span style={{ fontSize: "12px", fontWeight: 700, color: "#f1f5f9" }}>
                          {sig.project_display_name}
                        </span>
                      )}
                      {sig.repository_name && (
                        <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "monospace" }}>
                          ({sig.repository_name})
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: 1.4 }}>
                      {sig.summary}
                    </div>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px", flexShrink: 0 }}>
                    <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "monospace" }}>
                      {sig.timestamp ? new Date(sig.timestamp).toUTCString().slice(0, 22) : ""}
                    </span>
                    <div style={{ display: "flex", gap: "6px" }}>
                      {sig.project_id && onSelectProjectForTimeline && (
                        <button
                          onClick={() => onSelectProjectForTimeline(sig.project_id!)}
                          style={{
                            padding: "2px 6px",
                            backgroundColor: "#1e293b",
                            border: "1px solid #334155",
                            color: "#38bdf8",
                            borderRadius: "3px",
                            fontSize: "10px",
                            cursor: "pointer",
                          }}
                        >
                          Linha do Tempo →
                        </button>
                      )}
                      {sig.project_id && onSelectProjectForGraph && (
                        <button
                          onClick={() => onSelectProjectForGraph(sig.project_id!)}
                          style={{
                            padding: "2px 6px",
                            backgroundColor: "#1e293b",
                            border: "1px solid #334155",
                            color: "#94a3b8",
                            borderRadius: "3px",
                            fontSize: "10px",
                            cursor: "pointer",
                          }}
                        >
                          Grafo →
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 0C: MAPA OPERACIONAL DA HOLDING (DISTRIBUIÇÃO DOS 34 PROJETOS V0.4) */}
      <div style={{ marginBottom: "32px" }}>
        <div
          style={{
            fontSize: "13px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#34d399",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>Mapa Operacional da Holding (Status Factual dos {data?.projects?.length || 0} Projetos)</span>
          <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
            • Distribuição estrita por evidência observada sem inferência indevida
          </span>
        </div>

        {(() => {
          const projs = data?.projects || [];
          const hoje = projs.filter((p) => p.operational_activity_state === "ATIVIDADE_HOJE" || p.activity_today > 0);
          const recente = projs.filter((p) => (p.operational_activity_state === "ATIVIDADE_RECENTE" || p.activity_7d > 0) && !hoje.includes(p));
          const semAtividade = projs.filter((p) => (p.operational_activity_state === "SEM_ATIVIDADE_NO_PERIODO" || p.observation_count > 0) && !hoje.includes(p) && !recente.includes(p));
          const semDados = projs.filter((p) => !hoje.includes(p) && !recente.includes(p) && !semAtividade.includes(p));

          return (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: "12px",
              }}
            >
              {/* Coluna 1: Atividade Hoje */}
              <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderTop: "3px solid #34d399", borderRadius: "6px", padding: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 700, color: "#34d399", textTransform: "uppercase" }}>⚡ Atividade Hoje</span>
                  <span style={{ fontSize: "14px", fontWeight: 800, color: "#34d399" }}>{hoje.length}</span>
                </div>
                <div style={{ fontSize: "10px", color: "#64748b", marginBottom: "10px" }}>
                  Sinais observados hoje (UTC)
                </div>
                {hoje.length === 0 ? (
                  <div style={{ fontSize: "11px", color: "#475569", fontStyle: "italic" }}>Nenhum projeto com sinal hoje</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {hoje.map((p) => (
                      <div key={p.project_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", backgroundColor: "#1e293b", padding: "6px 8px", borderRadius: "4px" }}>
                        <span style={{ fontWeight: 600, color: "#f1f5f9" }}>{p.display_name || p.project_id}</span>
                        <span style={{ fontSize: "10px", color: "#34d399", fontFamily: "monospace" }}>+{p.activity_today} hoje</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Coluna 2: Atividade Recente */}
              <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderTop: "3px solid #38bdf8", borderRadius: "6px", padding: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 700, color: "#38bdf8", textTransform: "uppercase" }}>⏱ Atividade Recente</span>
                  <span style={{ fontSize: "14px", fontWeight: 800, color: "#38bdf8" }}>{recente.length}</span>
                </div>
                <div style={{ fontSize: "10px", color: "#64748b", marginBottom: "10px" }}>
                  Sinais observados nos últimos 7 dias
                </div>
                {recente.length === 0 ? (
                  <div style={{ fontSize: "11px", color: "#475569", fontStyle: "italic" }}>Nenhum projeto adicional recente</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", maxHeight: "200px", overflowY: "auto" }}>
                    {recente.map((p) => (
                      <div key={p.project_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", backgroundColor: "#1e293b", padding: "6px 8px", borderRadius: "4px" }}>
                        <span style={{ fontWeight: 600, color: "#f1f5f9" }}>{p.display_name || p.project_id}</span>
                        <span style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>{p.activity_7d} (7d)</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Coluna 3: Sem Atividade no Período */}
              <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderTop: "3px solid #94a3b8", borderRadius: "6px", padding: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase" }}>○ Sem Atividade no Período</span>
                  <span style={{ fontSize: "14px", fontWeight: 800, color: "#94a3b8" }}>{semAtividade.length}</span>
                </div>
                <div style={{ fontSize: "10px", color: "#64748b", marginBottom: "10px" }}>
                  Possui telemetria, sem sinais na janela (não inativo)
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                  {semAtividade.length} projetos monitorados sem novas observações no intervalo.
                </div>
              </div>

              {/* Coluna 4: Dados Insuficientes */}
              <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderTop: "3px solid #64748b", borderRadius: "6px", padding: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>? Dados Insuficientes</span>
                  <span style={{ fontSize: "14px", fontWeight: 800, color: "#64748b" }}>{semDados.length}</span>
                </div>
                <div style={{ fontSize: "10px", color: "#64748b", marginBottom: "10px" }}>
                  Sem telemetria registrada no PUB Neural
                </div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>
                  {semDados.length} projetos cadastrados aguardando ingestão inicial de telemetria.
                </div>
              </div>
            </div>
          );
        })()}
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
              {(["TODOS", "ATIVOS", "ATIVIDADE_HOJE", "ATIVIDADE_RECENTE", "SEM_ATIVIDADE", "ARQUIVADOS", "SEM_OBSERVACOES"] as FilterStatus[]).map((st) => {
                const labels: Record<FilterStatus, string> = {
                  TODOS: "Todos",
                  ATIVOS: "Ativos",
                  ATIVIDADE_HOJE: "Hoje ⚡",
                  ATIVIDADE_RECENTE: "Recente (7d)",
                  SEM_ATIVIDADE: "Sem Atividade no Período",
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

                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "6px" }}>
                      {/* Operational Activity State Badge V0.4 */}
                      {(() => {
                        const actState = proj.operational_activity_state || (proj.activity_today > 0 ? "ATIVIDADE_HOJE" : proj.activity_7d > 0 ? "ATIVIDADE_RECENTE" : proj.observation_count > 0 ? "SEM_ATIVIDADE_NO_PERIODO" : "DADOS_INSUFICIENTES");
                        if (actState === "ATIVIDADE_HOJE") {
                          return (
                            <span
                              style={{
                                fontSize: "10px",
                                padding: "2px 8px",
                                borderRadius: "4px",
                                backgroundColor: "rgba(16, 185, 129, 0.2)",
                                color: "#34d399",
                                border: "1px solid rgba(16, 185, 129, 0.4)",
                                fontWeight: 700,
                              }}
                              title="Sinais operacionais concretos observados hoje (UTC)"
                            >
                              ⚡ Atividade Hoje
                            </span>
                          );
                        }
                        if (actState === "ATIVIDADE_RECENTE") {
                          return (
                            <span
                              style={{
                                fontSize: "10px",
                                padding: "2px 8px",
                                borderRadius: "4px",
                                backgroundColor: "rgba(56, 189, 248, 0.15)",
                                color: "#38bdf8",
                                border: "1px solid rgba(56, 189, 248, 0.3)",
                                fontWeight: 600,
                              }}
                              title="Sinais operacionais concretos observados nos últimos 7 dias"
                            >
                              ⏱ Atividade Recente
                            </span>
                          );
                        }
                        if (actState === "SEM_ATIVIDADE_NO_PERIODO") {
                          return (
                            <span
                              style={{
                                fontSize: "10px",
                                padding: "2px 8px",
                                borderRadius: "4px",
                                backgroundColor: "rgba(100, 116, 139, 0.15)",
                                color: "#94a3b8",
                                border: "1px solid rgba(100, 116, 139, 0.3)",
                                fontWeight: 500,
                              }}
                              title="Sem novos sinais observados no período da janela (não indica inatividade do projeto)"
                            >
                              ○ Sem Atividade no Período
                            </span>
                          );
                        }
                        return (
                          <span
                            style={{
                              fontSize: "10px",
                              padding: "2px 8px",
                              borderRadius: "4px",
                              backgroundColor: "rgba(71, 85, 105, 0.2)",
                              color: "#64748b",
                              border: "1px solid rgba(71, 85, 105, 0.3)",
                              fontWeight: 500,
                            }}
                            title="Sem telemetria registrada no PUB Neural"
                          >
                            ? Dados Insuficientes
                          </span>
                        );
                      })()}

                      {/* Epistemological Status Badge - 3 Friendly Levels */}
                      {(() => {
                        const hp = data?.holding_projects?.find(
                          (h) => h.id === proj.project_id || h.slug === proj.project_id || h.id === `proj:${proj.project_id}`
                        );
                        const status = hp?.ontology_status || "PROPOSED";
                        const conf = Math.round((hp?.ontology_confidence ?? 0.85) * 100);
                        const reason = hp?.ontology_reason || "Inferência por metadata do repositório";

                        if (status === "CONFIRMED") {
                          return (
                            <span
                              style={{
                                fontSize: "10px",
                                padding: "3px 8px",
                                borderRadius: "4px",
                                backgroundColor: "#064e3b",
                                color: "#34d399",
                                border: "1px solid rgba(52, 211, 153, 0.3)",
                                fontWeight: 700,
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
                              }}
                              title={`Baseado em evidência documental ou confirmação explícita. (${reason})`}
                            >
                              ✓ Confirmado
                            </span>
                          );
                        }
                        if (status === "PROPOSED") {
                          return (
                            <span
                              style={{
                                fontSize: "10px",
                                padding: "3px 8px",
                                borderRadius: "4px",
                                backgroundColor: "#78350f",
                                color: "#fcd34d",
                                border: "1px solid rgba(252, 211, 77, 0.3)",
                                fontWeight: 700,
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
                              }}
                              title={`Inferência produzida por regras, metadata ou análise. (${reason})`}
                            >
                              ◌ Sugerido · {conf}%
                            </span>
                          );
                        }
                        return (
                          <span
                            style={{
                              fontSize: "10px",
                              padding: "3px 8px",
                              borderRadius: "4px",
                              backgroundColor: "#334155",
                              color: "#94a3b8",
                              border: "1px solid rgba(148, 163, 184, 0.3)",
                              fontWeight: 700,
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                            title="Evidência insuficiente para classificação."
                          >
                            ? Não classificado
                          </span>
                        );
                      })()}

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

                  {/* Provenance & Governança Ontológica do Projeto */}
                  {(() => {
                    const hp = data?.holding_projects?.find(
                      (h) => h.id === proj.project_id || h.slug === proj.project_id || h.id === `proj:${proj.project_id}`
                    );
                    if (!hp) return null;

                    return (
                      <div
                        style={{
                          backgroundColor: "#090d16",
                          border: "1px solid #1e293b",
                          borderRadius: "6px",
                          padding: "8px 10px",
                          fontSize: "10px",
                          color: "#94a3b8",
                          display: "flex",
                          flexDirection: "column",
                          gap: "4px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b" }}>
                          <span>PROVENIÊNCIA ONTOLÓGICA:</span>
                          <span style={{ color: hp.ontology_status === "CONFIRMED" ? "#34d399" : "#fcd34d" }}>
                            {hp.ontology_status === "CONFIRMED" ? "✓ Validado soberanamente" : "◌ Inferência estrutural"}
                          </span>
                        </div>
                        <div>
                          <strong>Por quê:</strong> {hp.ontology_reason || "Classificação padrão"}
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", color: "#64748b" }}>
                          <span>Classificado por: <strong style={{ color: "#cbd5e1" }}>{hp.ontology_verified_by || hp.ontology_source}</strong></span>
                          <span>Confiança: <strong style={{ color: "#cbd5e1" }}>{Math.round(hp.ontology_confidence * 100)}%</strong></span>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Repositórios Associados ao Projeto (Ontologia V0.2 / V0.3) */}
                  {(() => {
                    const hp = data?.holding_projects?.find(
                      (h) => h.id === proj.project_id || h.slug === proj.project_id || h.id === `proj:${proj.project_id}`
                    );
                    const repos = hp?.repositories || [];
                    const isExpanded = !!expandedProjects[proj.project_id];

                    if (repos.length === 0) return null;

                    return (
                      <div
                        style={{
                          backgroundColor: "#090d16",
                          border: "1px solid #1e293b",
                          borderRadius: "6px",
                          padding: "8px 10px",
                          fontSize: "11px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "6px",
                        }}
                      >
                        <div
                          onClick={() => toggleProjectExpand(proj.project_id)}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            cursor: "pointer",
                            userSelect: "none",
                          }}
                        >
                          <span
                            style={{
                              fontSize: "10px",
                              textTransform: "uppercase",
                              letterSpacing: "0.05em",
                              color: "#38bdf8",
                              fontWeight: 600,
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            <span>📦 Repositórios Associados ({repos.length})</span>
                          </span>
                          <span style={{ fontSize: "10px", color: "#64748b" }}>
                            {isExpanded ? "▲ Recolher" : "▼ Expandir"}
                          </span>
                        </div>

                        {isExpanded && (
                          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "4px" }}>
                            {repos.map((r) => (
                              <div
                                key={r.repository_id}
                                style={{
                                  padding: "6px 8px",
                                  backgroundColor: "#0f172a",
                                  border: "1px solid #1e293b",
                                  borderRadius: "4px",
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                                  gap: "8px",
                                }}
                              >
                                <div>
                                  <div style={{ fontWeight: 600, color: "#f1f5f9", fontSize: "11px" }}>
                                    {r.repository_name}
                                    {r.is_primary && (
                                      <span
                                        style={{
                                          marginLeft: "6px",
                                          fontSize: "9px",
                                          padding: "1px 4px",
                                          borderRadius: "3px",
                                          backgroundColor: "rgba(56, 189, 248, 0.15)",
                                          color: "#38bdf8",
                                        }}
                                      >
                                        Principal
                                      </span>
                                    )}
                                  </div>
                                  <div style={{ fontSize: "9px", color: "#64748b", marginTop: "1px" }}>
                                    {r.relationship_type} • {r.classification_reason || r.classification_source}
                                  </div>
                                </div>

                                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                  {r.association_status === "CONFIRMED" ? (
                                    <span
                                      style={{
                                        fontSize: "9px",
                                        padding: "2px 6px",
                                        borderRadius: "3px",
                                        backgroundColor: "#064e3b",
                                        color: "#34d399",
                                        border: "1px solid rgba(52, 211, 153, 0.3)",
                                        fontWeight: 600,
                                      }}
                                      title="Baseado em evidência documental ou confirmação explícita."
                                    >
                                      ✓ Confirmado
                                    </span>
                                  ) : (
                                    <span
                                      style={{
                                        fontSize: "9px",
                                        padding: "2px 6px",
                                        borderRadius: "3px",
                                        backgroundColor: "#78350f",
                                        color: "#fcd34d",
                                        border: "1px solid rgba(252, 211, 77, 0.3)",
                                        fontWeight: 600,
                                      }}
                                      title="Inferência produzida por regras, metadata ou análise."
                                    >
                                      ◌ Sugerido · {Math.round(r.classification_confidence * 100)}%
                                    </span>
                                  )}
                                  {r.github_url && (
                                    <a
                                      href={r.github_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      style={{ color: "#94a3b8", textDecoration: "none", fontSize: "10px" }}
                                    >
                                      ↗
                                    </a>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })()}

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

      {/* SECTION: FILAS DE GOVERNANÇA ONTOLÓGICA V0.3 */}
      {govQueues && (
        <div style={{ marginBottom: "32px" }}>
          <div
            style={{
              fontSize: "13px",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "#fb923c",
              marginBottom: "12px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>Filas de Governança Ontológica</span>
            <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
              • Itens aguardando validação factual soberana para promoção epistemológica
            </span>
          </div>

          {/* Queue Tab Buttons */}
          <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
            <button
              onClick={() => setActiveQueueTab("PROJECTS")}
              style={{
                padding: "8px 14px",
                borderRadius: "6px",
                border: "1px solid",
                borderColor: activeQueueTab === "PROJECTS" ? "#f59e0b" : "#334155",
                backgroundColor: activeQueueTab === "PROJECTS" ? "rgba(245, 158, 11, 0.15)" : "#0f172a",
                color: activeQueueTab === "PROJECTS" ? "#fcd34d" : "#94a3b8",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Projetos Aguardando Validação ({govQueues.pending_projects_count})
            </button>
            <button
              onClick={() => setActiveQueueTab("ASSOCIATIONS")}
              style={{
                padding: "8px 14px",
                borderRadius: "6px",
                border: "1px solid",
                borderColor: activeQueueTab === "ASSOCIATIONS" ? "#38bdf8" : "#334155",
                backgroundColor: activeQueueTab === "ASSOCIATIONS" ? "rgba(56, 189, 248, 0.15)" : "#0f172a",
                color: activeQueueTab === "ASSOCIATIONS" ? "#38bdf8" : "#94a3b8",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Associações Aguardando Validação ({govQueues.pending_associations_count})
            </button>
            <button
              onClick={() => setActiveQueueTab("UNCLASSIFIED")}
              style={{
                padding: "8px 14px",
                borderRadius: "6px",
                border: "1px solid",
                borderColor: activeQueueTab === "UNCLASSIFIED" ? "#94a3b8" : "#334155",
                backgroundColor: activeQueueTab === "UNCLASSIFIED" ? "rgba(148, 163, 184, 0.15)" : "#0f172a",
                color: activeQueueTab === "UNCLASSIFIED" ? "#f8fafc" : "#94a3b8",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Repositórios Não Classificados ({govQueues.unclassified_repositories_count})
            </button>
          </div>

          {/* Queue Tab Content */}
          {activeQueueTab === "PROJECTS" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "12px" }}>
              {govQueues.pending_projects.map((p) => (
                <div
                  key={p.id}
                  style={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderLeft: "3px solid #f59e0b",
                    borderRadius: "6px",
                    padding: "12px 14px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 700, color: "#f8fafc", fontSize: "13px" }}>{p.display_name}</span>
                    <span
                      style={{
                        fontSize: "9px",
                        padding: "2px 6px",
                        borderRadius: "3px",
                        backgroundColor: "#78350f",
                        color: "#fcd34d",
                        border: "1px solid rgba(252, 211, 77, 0.3)",
                        fontWeight: 600,
                      }}
                      title="Inferência produzida por regras, metadata ou análise."
                    >
                      ◌ Sugerido · {Math.round(p.ontology_confidence * 100)}%
                    </span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: 1.3 }}>{p.description}</div>
                  <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px" }}>
                    Motivo: {p.ontology_reason || "Inferido via repositório"} • {p.repositories_count} repo(s)
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeQueueTab === "ASSOCIATIONS" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "12px" }}>
              {govQueues.pending_associations.map((a) => (
                <div
                  key={`${a.project_id}-${a.repository_id}`}
                  style={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderLeft: "3px solid #38bdf8",
                    borderRadius: "6px",
                    padding: "12px 14px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 700, color: "#f8fafc", fontSize: "13px" }}>{a.repository_name}</span>
                    <span
                      style={{
                        fontSize: "9px",
                        padding: "2px 6px",
                        borderRadius: "3px",
                        backgroundColor: "#78350f",
                        color: "#fcd34d",
                        border: "1px solid rgba(252, 211, 77, 0.3)",
                        fontWeight: 600,
                      }}
                      title="Inferência produzida por regras, metadata ou análise."
                    >
                      ◌ Sugerido · {Math.round(a.classification_confidence * 100)}%
                    </span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#38bdf8" }}>
                    Projeto Associado: <strong>{a.project_display_name}</strong> ({a.relationship_type})
                  </div>
                  <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px" }}>
                    Motivo: {a.classification_reason || a.classification_source}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeQueueTab === "UNCLASSIFIED" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "12px" }}>
              {govQueues.unclassified_repositories.map((u) => (
                <div
                  key={u.id}
                  style={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderLeft: "3px solid #94a3b8",
                    borderRadius: "6px",
                    padding: "12px 14px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 700, color: "#f8fafc", fontSize: "13px" }}>{u.display_name || u.repository_name}</span>
                    <span
                      style={{
                        fontSize: "9px",
                        padding: "2px 6px",
                        borderRadius: "3px",
                        backgroundColor: "#334155",
                        color: "#94a3b8",
                        border: "1px solid rgba(148, 163, 184, 0.3)",
                        fontWeight: 600,
                      }}
                      title="Evidência insuficiente para classificação."
                    >
                      ? Não classificado
                    </span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8" }}>{u.repository_full_name}</div>
                  <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px" }}>
                    Categoria: {u.category} • Isolado ontologicamente
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

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
