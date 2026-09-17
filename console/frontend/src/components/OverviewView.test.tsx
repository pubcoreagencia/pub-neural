import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OverviewView } from "./OverviewView";
import { NeuralAPI } from "../api/client";

vi.mock("../api/client", () => ({
  NeuralAPI: {
    getOverview: vi.fn(),
    getGovernanceReview: vi.fn(),
    getUnclassifiedRepositories: vi.fn(),
    getGovernanceOntologyQueues: vi.fn(),
    getActivity: vi.fn(),
  },
}));

describe("OverviewView Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(NeuralAPI.getUnclassifiedRepositories).mockResolvedValue([]);
    vi.mocked(NeuralAPI.getActivity).mockResolvedValue({
      window_days: 14,
      total_signals: 1,
      projects_with_activity_today: 1,
      projects_with_activity_7d: 1,
      signals: [
        {
          id: "obs:1",
          project_id: "pub-ecom",
          project_display_name: "PUB E-Commerce",
          repository_id: "pub-ecom",
          repository_name: "pubcoreagencia/pub-ecom",
          activity_type: "REPOSITORY_OBSERVED",
          timestamp: "2026-09-16T12:00:00Z",
          source: "neural_repository_observations",
          summary: "Observed commit a1b2c3d on branch main",
          locator: "pubcoreagencia/pub-ecom@a1b2c3d",
          evidence_preview: null,
          event_id: null,
        },
      ],
    });
    vi.mocked(NeuralAPI.getGovernanceReview).mockResolvedValue({
      generated_at: "2026-09-16T12:00:00Z",
      candidates_count: 0,
      candidates: [],
    });
    vi.mocked(NeuralAPI.getGovernanceOntologyQueues).mockResolvedValue({
      pending_projects_count: 1,
      pending_projects: [
        {
          id: "proj:pub-trade",
          slug: "pub-trade",
          display_name: "PUB Trade",
          description: "Projeto proposto",
          project_type: "PRODUCT",
          lifecycle_status: "PROPOSTO",
          strategic_priority: "PADRAO",
          ontology_status: "PROPOSED",
          ontology_source: "RULE",
          ontology_confidence: 0.85,
          ontology_reason: "Inferido do repo",
          repositories_count: 1,
        },
      ],
      pending_associations_count: 1,
      pending_associations: [
        {
          project_id: "proj:pub-ecom",
          project_display_name: "PUB E-Commerce",
          repository_id: "pub-ecom-landing",
          repository_name: "pub-ecom-landing",
          repository_display_name: "pub-ecom-landing",
          relationship_type: "LANDING_PAGE",
          is_primary: false,
          association_status: "PROPOSED",
          classification_source: "RULE",
          classification_confidence: 0.9,
          classification_reason: "Prefix match",
        },
      ],
      unclassified_repositories_count: 1,
      unclassified_repositories: [
        {
          id: "pub-github-mcp",
          repository_full_name: "pubcoreagencia/pub-github-mcp",
          repository_name: "pub-github-mcp",
          display_name: "pub-github-mcp",
          description: "Standalone MCP repository",
          category: "INFRAESTRUTURA",
          lifecycle_status: "ATIVO",
          is_active: true,
          is_archived: false,
          is_private: true,
          monitoring_enabled: true,
          strategic_priority: "PADRAO",
          github_url: "https://github.com/pubcoreagencia/pub-github-mcp",
          created_at: "2026-09-16T00:00:00Z",
          updated_at: "2026-09-16T00:00:00Z",
          last_discovered_at: "2026-09-16T00:00:00Z",
        },
      ],
    });
  });

  it("renders loading state then operational overview data", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T04:00:00Z",
      window_days: 7,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      executive_summary: {
        total_projects: 1,
        active_projects: 1,
        monitored_repositories: 1,
        recent_observations_7d: 20,
        events_today: 5,
        candidate_knowledge_count: 0,
        adopted_knowledge_count: 8,
        neural_health: "SAUDAVEL",
      },
      projects: [
        {
          project_id: "pub-ecom",
          display_name: "PUB E-Commerce",
          category: "ECOMMERCE",
          is_active: true,
          is_archived: false,
          observed_repository_count: 1,
          observation_count: 42,
          activity_today: 5,
          activity_7d: 20,
          last_observation_at: "2026-09-16T03:00:00Z",
          active_node_count: 8,
          project_state: "ATIVO_OBSERVADO",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
      ],
      daily_activity: [
        {
          day: "2026-09-16",
          project_id: "pub-ecom",
          observed_count: 5,
        },
      ],
    });

    render(<OverviewView />);

    expect(screen.getByText(/Carregando Cockpit Operacional PUB Neural/i)).toBeDefined();

    await waitFor(() => {
      expect(screen.getAllByText(/PUB E-Commerce/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/Banco de Dados: SAUDÁVEL/i)).toBeDefined();
      expect(screen.getByText(/Projetores: SAUDÁVEL/i)).toBeDefined();
      expect(screen.getByText("42")).toBeDefined();
      expect(screen.getByText(/Panorama Executivo da Holding/i)).toBeDefined();
    });
  });

  it("renders distinct project without repository observations without failing", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T04:00:00Z",
      window_days: 7,
      database_health: "HEALTHY",
      projector_health: "DEGRADED",
      executive_summary: {
        total_projects: 1,
        active_projects: 1,
        monitored_repositories: 1,
        recent_observations_7d: 0,
        events_today: 0,
        candidate_knowledge_count: 0,
        adopted_knowledge_count: 14,
        neural_health: "DEGRADADO",
      },
      projects: [
        {
          project_id: "pub-holding",
          display_name: "PUB Holding",
          category: "HOLDING",
          is_active: true,
          is_archived: false,
          observed_repository_count: 0,
          observation_count: 0,
          activity_today: 0,
          activity_7d: 0,
          last_observation_at: null,
          active_node_count: 14,
          project_state: "SEM_OBSERVACOES",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
      ],
      daily_activity: [
        {
          day: "2026-09-16",
          project_id: "pub-holding",
          observed_count: 0,
        },
      ],
    });

    render(<OverviewView />);

    await waitFor(() => {
      expect(screen.getByText(/Projetores: DEGRADADO/i)).toBeDefined();
      expect(screen.getAllByText("PUB Holding").length).toBeGreaterThan(0);
      expect(screen.getByText("Sem observações registradas")).toBeDefined();
    });
  });

  it("renders V0.2-A contract: project_state, blocked_nodes, latest_signal, and no synthetic progress", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T05:00:00Z",
      window_days: 14,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      executive_summary: {
        total_projects: 3,
        active_projects: 2,
        monitored_repositories: 1,
        recent_observations_7d: 15,
        events_today: 3,
        candidate_knowledge_count: 0,
        adopted_knowledge_count: 20,
        neural_health: "SAUDAVEL",
      },
      projects: [
        {
          project_id: "pub-ecom",
          display_name: "PUB E-Commerce",
          is_active: true,
          is_archived: false,
          observed_repository_count: 1,
          observation_count: 50,
          activity_today: 3,
          activity_7d: 15,
          last_observation_at: "2026-09-16T04:30:00Z",
          active_node_count: 12,
          project_state: "ATIVO_OBSERVADO",
          blocked_nodes_count: 0,
          latest_signal: {
            type: "REPOSITORY_OBSERVED",
            timestamp: "2026-09-16T04:30:00Z",
            summary: "Observed commit a1b2c3d on branch main",
            source: "neural_repository_observations",
            locator: "pub-holding/pub-ecom@a1b2c3d",
          },
        },
        {
          project_id: "pub-core",
          display_name: "PUB Core",
          is_active: true,
          is_archived: false,
          observed_repository_count: 0,
          observation_count: 0,
          activity_today: 0,
          activity_7d: 0,
          last_observation_at: null,
          active_node_count: 8,
          project_state: "SEM_OBSERVACOES",
          blocked_nodes_count: 2,
          latest_signal: {
            type: "TASK_EXPERIENCE_RECORDED",
            timestamp: "2026-09-16T04:15:00Z",
            summary: "Task task-102 completed with status SUCCESS: Upgrade auth module",
            source: "neural_events",
            locator: "evt-uuid-456",
          },
        },
        {
          project_id: "pub-empty",
          display_name: "PUB Empty",
          is_active: false,
          is_archived: true,
          observed_repository_count: 0,
          observation_count: 0,
          activity_today: 0,
          activity_7d: 0,
          last_observation_at: null,
          active_node_count: 0,
          project_state: "ARQUIVADO",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
      ],
      daily_activity: [],
    });

    render(<OverviewView />);

    await waitFor(() => {
      // 1. Project States (friendly states: Ativo, Sem observações registradas, Arquivado)
      expect(screen.getByText("Ativo")).toBeDefined();
      expect(screen.getByText("Sem observações registradas")).toBeDefined();
      expect(screen.getByText("Arquivado")).toBeDefined();

      // 2. Blocked Nodes
      expect(screen.getByText("Nós Bloqueados: 2")).toBeDefined();
      expect(screen.getAllByText("Nós Bloqueados: 0").length).toBeGreaterThanOrEqual(2);

      // 3. Operational Signals (appears in project card and/or holding activity feed)
      expect(screen.getAllByText("TELEMETRIA").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Observed commit a1b2c3d on branch main").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("pub-holding/pub-ecom@a1b2c3d")).toBeDefined();

      expect(screen.getByText("SINAL DE TAREFA")).toBeDefined();
      expect(screen.getByText("Task task-102 completed with status SUCCESS: Upgrade auth module")).toBeDefined();
      expect(screen.getByText("evt-uuid-456")).toBeDefined();

      expect(screen.getByText("Nenhum sinal operacional registrado")).toBeDefined();

      // 4. Invariants: NO synthetic progress or project health
      expect(screen.queryByText(/Project Progress/i)).toBeNull();
      expect(screen.queryByText(/Progress:/i)).toBeNull();
      expect(screen.queryByText(/Project Health:/i)).toBeNull();
    });
  });

  it("renders candidate knowledge awaiting governance review", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T04:00:00Z",
      window_days: 7,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      projects: [],
      daily_activity: [],
    });

    vi.mocked(NeuralAPI.getGovernanceReview).mockResolvedValueOnce({
      generated_at: "2026-09-16T12:00:00Z",
      candidates_count: 1,
      candidates: [
        {
          id: "finding:pub-neural:task-test:1",
          entity_type: "LESSON",
          title: "Supabase pgcrypto search_path configuration",
          summary: "Must include extensions in search path",
          content: "Detailed content",
          promotion_state: "CANDIDATE",
          promotion_reason: "Discovered during task-test",
          conflict_state: "RESOLVED",
          scope: "PROJECT",
          project_id: "pub-neural",
          trust_zone: "tz_internal_holding",
          originating_event_id: "evt-001",
          originating_event_type: "TASK_EXPERIENCE_RECORDED",
          proposed_by_actor_id: "autonomous-gate",
          proposed_by_actor_role: "AGENT",
          derived_from_experience_id: "experience:pub-neural:task-test",
          created_at: "2026-09-16T12:00:00Z",
          evidence_count: 1,
        },
      ],
    });

    render(<OverviewView />);

    await waitFor(() => {
      expect(screen.getByText(/Conhecimento Candidato Aguardando Governança \(1\)/i)).toBeDefined();
      expect(screen.getByText("Supabase pgcrypto search_path configuration")).toBeDefined();
      expect(screen.getByText("LESSON • CANDIDATO")).toBeDefined();
      expect(screen.getByText(/Proposto por: autonomous-gate \(AGENT\)/i)).toBeDefined();
    });
  });

  it("renders Project Ontology V0.2: Holding Projects, Repositories tree, and Unclassified Repositories", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T12:00:00Z",
      window_days: 14,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      executive_summary: {
        total_holding_projects: 34,
        total_repositories: 57,
        multi_repo_projects_count: 13,
        unclassified_repositories_count: 1,
        confirmed_associations_count: 17,
        proposed_associations_count: 39,
        confirmed_projects_count: 6,
        proposed_projects_count: 28,
        unknown_projects_count: 0,
        active_projects: 34,
        monitored_repositories: 57,
        recent_observations_7d: 1,
        events_today: 0,
        candidate_knowledge_count: 0,
        adopted_knowledge_count: 4,
        neural_health: "SAUDAVEL",
      },
      projects: [
        {
          project_id: "pub-ecom",
          display_name: "PUB E-Commerce",
          is_active: true,
          is_archived: false,
          observed_repository_count: 1,
          observation_count: 5,
          activity_today: 0,
          activity_7d: 1,
          last_observation_at: "2026-09-16T10:00:00Z",
          active_node_count: 2,
          project_state: "ATIVO_OBSERVADO",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
      ],
      holding_projects: [
        {
          id: "proj:pub-ecom",
          slug: "pub-ecom",
          display_name: "PUB E-Commerce",
          description: "Hub de e-commerce",
          project_type: "PRODUCT",
          lifecycle_status: "ATIVO",
          is_active: true,
          is_archived: false,
          strategic_priority: "CRITICA",
          owner_scope: "pubcoreagencia",
          repositories_count: 2,
          confirmed_repositories_count: 1,
          proposed_repositories_count: 1,
          active_knowledge_nodes_count: 2,
          recent_observations_7d: 1,
          ontology_status: "CONFIRMED",
          ontology_source: "DOCUMENTATION",
          ontology_confidence: 1.0,
          ontology_reason: "Platform core",
          ontology_verified_at: "2026-09-16T00:00:00Z",
          ontology_verified_by: "actor:auditor:console-operator",
          repositories: [
            {
              project_id: "proj:pub-ecom",
              repository_id: "pub-ecom",
              repository_name: "pub-ecom",
              display_name: "pub-ecom",
              category: "ECOMMERCE",
              relationship_type: "PRIMARY",
              is_primary: true,
              association_status: "CONFIRMED",
              classification_source: "DOCUMENTATION",
              classification_confidence: 1.0,
              classification_reason: "Monorepo core",
              github_url: "https://github.com/pubcoreagencia/pub-ecom",
            },
            {
              project_id: "proj:pub-ecom",
              repository_id: "pub-ecom-landing",
              repository_name: "pub-ecom-landing",
              display_name: "pub-ecom-landing",
              category: "FRONTEND",
              relationship_type: "LANDING_PAGE",
              is_primary: false,
              association_status: "PROPOSED",
              classification_source: "RULE",
              classification_confidence: 0.9,
              classification_reason: "Prefix match",
              github_url: "https://github.com/pubcoreagencia/pub-ecom-landing",
            },
          ],
          created_at: "2026-09-16T00:00:00Z",
          updated_at: "2026-09-16T00:00:00Z",
        },
      ],
      daily_activity: [],
    });

    vi.mocked(NeuralAPI.getUnclassifiedRepositories).mockResolvedValueOnce([
      {
        id: "pub-github-mcp",
        repository_full_name: "pubcoreagencia/pub-github-mcp",
        repository_name: "pub-github-mcp",
        display_name: "pub-github-mcp",
        description: "Standalone MCP repository",
        category: "INFRAESTRUTURA",
        lifecycle_status: "ATIVO",
        is_active: true,
        is_archived: false,
        is_private: true,
        monitoring_enabled: true,
        strategic_priority: "PADRAO",
        github_url: "https://github.com/pubcoreagencia/pub-github-mcp",
        created_at: "2026-09-16T00:00:00Z",
        updated_at: "2026-09-16T00:00:00Z",
        last_discovered_at: "2026-09-16T00:00:00Z",
      },
    ]);

    render(<OverviewView />);

    await waitFor(() => {
      // 1. Executive Summary Epistemological Cards
      expect(screen.getByText("6")).toBeDefined();
      expect(screen.getByText("28")).toBeDefined();
      expect(screen.getByText("17")).toBeDefined();
      expect(screen.getByText("39")).toBeDefined();
      expect(screen.getByText("Projetos Confirmados")).toBeDefined();
      expect(screen.getByText("Projetos Sugeridos")).toBeDefined();

      // 2. Repositórios Associados toggle
      expect(screen.getByText(/Repositórios Associados \(2\)/i)).toBeDefined();

      // 3. Filas de Governança
      expect(screen.getByText(/Filas de Governança Ontológica/i)).toBeDefined();
      expect(screen.getByText(/Projetos Aguardando Validação \(1\)/i)).toBeDefined();
    });
  });

  it("renders V0.4 Operational Activity Intelligence: feed, filters, metric cards, and operational holding map", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T05:00:00Z",
      window_days: 14,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      executive_summary: {
        total_projects: 3,
        active_projects: 3,
        monitored_repositories: 2,
        recent_observations_7d: 12,
        events_today: 4,
        candidate_knowledge_count: 0,
        adopted_knowledge_count: 20,
        neural_health: "SAUDAVEL",
        projects_with_activity_today_count: 1,
        projects_with_activity_7d_count: 2,
      },
      projects: [
        {
          project_id: "pub-ecom",
          display_name: "PUB E-Commerce",
          is_active: true,
          is_archived: false,
          observed_repository_count: 1,
          observation_count: 50,
          activity_today: 3,
          activity_7d: 15,
          operational_activity_state: "ATIVIDADE_HOJE",
          last_observation_at: "2026-09-16T04:30:00Z",
          active_node_count: 12,
          project_state: "ATIVO_OBSERVADO",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
        {
          project_id: "pub-trade",
          display_name: "PUB Trade",
          is_active: true,
          is_archived: false,
          observed_repository_count: 1,
          observation_count: 20,
          activity_today: 0,
          activity_7d: 5,
          operational_activity_state: "ATIVIDADE_RECENTE",
          last_observation_at: "2026-09-14T04:30:00Z",
          active_node_count: 6,
          project_state: "ATIVO_OBSERVADO",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
        {
          project_id: "pub-docs",
          display_name: "PUB Docs",
          is_active: true,
          is_archived: false,
          observed_repository_count: 0,
          observation_count: 0,
          activity_today: 0,
          activity_7d: 0,
          operational_activity_state: "DADOS_INSUFICIENTES",
          last_observation_at: null,
          active_node_count: 2,
          project_state: "SEM_OBSERVACOES",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
      ],
      daily_activity: [],
    });

    render(<OverviewView />);

    await waitFor(() => {
      // 1. Executive Summary Activity Cards
      expect(screen.getByText("Atividade Hoje")).toBeDefined();
      expect(screen.getByText("Atividade 7 Dias")).toBeDefined();

      // 2. Section 0B: Activity Feed Header & Signals
      expect(screen.getByText(/Atividade Operacional da Holding/i)).toBeDefined();
      expect(screen.getByText("REPOSITORY_OBSERVED")).toBeDefined();
      expect(screen.getByText("Observed commit a1b2c3d on branch main")).toBeDefined();

      // 3. Section 0C: Holding Operational Map
      expect(screen.getByText(/Mapa Operacional da Holding/i)).toBeDefined();
      expect(screen.getAllByText(/⚡ Atividade Hoje/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/⏱ Atividade Recente/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/○ Sem Atividade no Período/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/Dados Insuficientes/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
