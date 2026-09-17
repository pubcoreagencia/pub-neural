# PUB NEURAL — GRAPH EXPLORER V0 SPECIFICATION
## Obsidian UX + Graphify Structural Capabilities + PUB Neural Canonical Cognition

**Status:** CANONICAL ARCHITECTURAL SPECIFICATION  
**Document ID:** `docs/GRAPH_EXPLORER_V0.md`  
**Consolidation Date:** 2026-09-17  
**Target:** Neural Console Frontend & Graph Query Backend  

---

## 1. Executive Summary

O **PUB Neural Graph Explorer V0** é a superfície visual e espacial nativa de exploração do grafo de conhecimento canônico da PUB Core Holding.

Ele sintetiza três pilares fundamentais:
1. **Sensação Espacial e Interativa do Obsidian:** Navegação fluida, zoom/pan orgânico, expansão progressiva por duplo-clique, física de grafos orientada a nós e conexões dinâmicas.
2. **Capacidades Estruturais e Topológicas do Graphify:** Detecção de comunidades (Louvain/Leiden), realce de dependências cruzadas (AST, chamadas, imports), agrupamento visual e identificação de nós centrais ("god-nodes").
3. **Cognição Canônica e Governança do PUB Neural:** Preservação estrita de proveniência (Commit SHA, linhas de código), linhagem temporal (bi-temporalidade `valid_from` vs `recorded_from`), classificação epistemológica (`EXTRACTED` vs `INFERRED`, `CANDIDATE` vs `VALIDATED`), e conformidade rigorosa com Trust Zones.

> [!IMPORTANT]
> **Princípio Central:**
> `Obsidian-like exploration + Graphify-like structural graph + PUB Neural canonical cognition.`  
> O resultado final não é um mero visualizador de banco de dados, mas um **mapa vivo do conhecimento da PUB Core Holding**, servindo de infraestrutura visual para o **Research Runtime**.

---

## 2. Auditoria do Frontend Atual do PUB Neural

### 2.1 Stack & Estrutura Técnica
- **Framework:** React 19 (`19.2.8`), TypeScript (`~6.0.2`), Vite 8 (`8.3.0`).
- **Linter & Testes:** Oxlint (`1.81.0`), Vitest (`5.0.0`), React Testing Library.
- **Biblioteca de Grafo Atual:** `@xyflow/react` (`12.11.6` - React Flow) acoplado com `@dagrejs/dagre` (`3.1.1`).
- **Navegação & Modos de Visualização:** O `App.tsx` chaveia entre `"overview"`, `"graph"` e `"timeline"`.
- **Layout Atual do Grafo:** Dagre hierárquico rígido Top-to-Bottom (`TB`) em `src/graph/layout.ts`. Cada nó tem tamanho estático fixo ($240 \times 110$ px).
- **Backend API Atual:**
  - `GET /api/v1/entities/{id}/neighborhood?depth=1|2&limit=50`: Executa CTE recursiva SQL limitada em `pub_neural.neural_edges` e faz merge em `pub_neural.neural_nodes`.
  - `GET /api/v1/entities/{id}`: Detalha o nó, metadados bi-temporais e citações exatas em `pub_neural.neural_evidence`.
  - `GET /api/v1/search?q=...`: Busca textual lexica em nós.

### 2.2 Diagnóstico & Limitações da UX Atual
1. **Layout Rígido (Dagre):** Força diagramação em árvore hierárquica. Não permite a sensação de "constelação cósmica" ou "rede de conhecimento" que o Obsidian oferece.
2. **Falta de Visualização Global (Global Graph):** O grafo só carrega se uma entidade específica for pré-selecionada. Não há visão ampla do universo interconectado de projetos da holding.
3. **Estilo "Card" vs "Ponto/Nó Conectivo":** Nós atuais são grandes cartões retangulares estáticos, tornando impossível renderizar mais de 50 nós na tela sem sobreposição severa e perda de legibilidade.
4. **Ausência de Física e Forças (Force-Directed Simulation):** Falta o algoritmo de atração e repulsão (física de molas) característico de grafos de conhecimento modernos.

---

## 3. Auditoria do Graphify (Frontend & UX de Referência)

Referência técnica: Graphify (`branch v8`, Commit `26b02b5`, Licença Apache-2.0).

- **Natureza da Engine:** Graphify é primariamente uma CLI Python que gera artefatos de dados (`graph.json`) estruturados contendo `nodes` (com labels de módulos, funções e comunidades) e `links` (arestas direcionadas tipadas).
- **Abordagem de Visualização:** O Graphify renderiza grafos usando WebGL/Canvas (baseado em bibliotecas de visualização force-directed 2D/3D ou D3-force).
- **Topologia de Comunidades:** Graphify calcula clusters através do algoritmo Louvain/Leiden, injetando `community_id` em cada nó e permitindo coloração de comunidades ou cascas convexas (convex hulls) agrupando submódulos.
- **Licença Apache-2.0:** Permite a livre reutilização de conceitos, contratos e algoritmos de mapeamento, exigindo preservação de atribuição caso código seja transposto.

---

## 4. Referência de UX do Obsidian Graph View

O Obsidian Graph View estabeleceu o padrão de excelência para navegação espacial em grafos de conhecimento. Comportamentos canônicos a serem adaptados:

| Dimensão | Comportamento Obsidian | Adaptação Canônica no PUB Neural |
| :--- | :--- | :--- |
| **Navegação** | Zoom contínuo suave, pan inercial e recentralização no duplo clique. | Zoom/Pan com física suave, reset para bounding box ativa. |
| **Física de Força** | Force-directed simulation (repulsão de Coulomb + atração de Hooke). | Simulação contínua com repulsão por tipo de entidade e gravidade central. |
| **Nós & Escala** | Círculos com diâmetro proporcional ao grau de conexões (in/out-degree). | Círculos dimensionados por conectividade e evidências (`evidence_count`). |
| **Hover & Foco** | Foco em 1 nó esmaece (dim) todo o grafo que não esteja no raio de 1-hop. | Realce da vizinhança direta com iluminação de arestas adjacentes e atenuação do fundo. |
| **Labels Dinâmicos** | Labels ocultam em zoom distante e revelam progressivamente em aproximação. | LOD (Level of Detail) semântico: distante = nó colorido; próximo = slug/título; hover = tooltip completo. |
| **Filtros em Tempo Real** | Filtros booleanos por pasta, tag e data de criação. | Filtros dinâmicos por `entity_type`, `relation_type`, `trust_zone`, `epistemic_state` e `project_id`. |
| **Expansão Local** | Slider de profundidade de vizinhos (1 a 5 hops). | Botão e atalho de expansão progressiva por nó clicado via API lazy loading. |

---

## 5. Requisitos de Experiência (UX Requirements)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PUB NEURAL CONSOLE                              │
├────────────────────────────────┬────────────────────────────────────────────┤
│ 1. FILTER & SEARCH TOOLBAR     │ 2. HUD & METRICS (Nodes, Edges, Density)   │
├────────────────────────────────┴────────────────────────────────────────────┤
│                                                                             │
│                                                                             │
│                               ✦ (PROJECT: pub-ecom)                        │
│                               │                                             │
│                               │ IMPLEMENTS (conf: 0.95)                     │
│                               ▼                                             │
│        ● ───────────────────► ● (RULE: zero-mutation) ◄─────────── ●        │
│    (DECISION)                 │                               (PATTERN)     │
│                               ▼ DERIVED_FROM                                │
│                               ● (EVIDENCE: L42-L80)                         │
│                                                                             │
│                                                                             │
├────────────────────────────────┬────────────────────────────────────────────┤
│ 3. MINI-MAP (Bottom Right)     │ 4. DETAIL INSPECTOR (Right Dock / Sliding) │
└────────────────────────────────┴────────────────────────────────────────────┘
```

1. **Modo Global Graph (Constelação da Holding):**
   - Carrega o backbone de entidades centrais: `HOLDING`, `PROJECT`, `REPOSITORY`, `DECISION` ratificadas e `RULE`.
   - Permite visualizar como os projetos se relacionam institucionalmente.
2. **Modo Focus Graph (Investigação Guiada):**
   - Centraliza em um nó selecionado (ex: um componente ou decisão).
   - Mostra vizinhos a 1 ou 2 hops com conexões estruturais e evidências vinculadas.
3. **Node Inspector Unificado:**
   - Exibe tipo, slug, estado de promoção (`CANDIDATE` / `VALIDATED` / `INSTITUTIONAL`), score de confiança, janelas temporais (`valid_from` vs `recorded_from`) e a lista de evidências de código que sustentam a entidade.
4. **Edge Inspector Unificado:**
   - Exibe a classificação relacional (`USES`, `DEPENDS_ON`, `CONTRADICTS`), proveniência (extrator AST vs inferência heurística), confiança e links para as linhas exatas do arquivo fonte.

---

## 6. Arquitetura do PUB Neural Graph Explorer

```text
                                 PUB NEURAL CONSOLE
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
 ┌──────────────┐                                                 ┌──────────────┐
 │  Graph View  │                                                 │ Research UI  │
 └──────┬───────┘                                                 └──────┬───────┘
        │                                                                │
        ▼                                                                ▼
 ┌───────────────────────────────────────────────────────────────────────────────┐
 │                       GRAPH EXPLORER ORCHESTRATOR                             │
 │   - State: activeSubGraph, selectedNodeId, selectedEdgeId, filterCriteria     │
 │   - Layout Engine: Force-Directed (D3-Force / WebGL) + Semantic Clustering    │
 │   - Incremental Cache: Local In-Memory Graph Index (O(1) neighbor lookups)    │
 └───────────────────────────────────────┬───────────────────────────────────────┘
                                         │
                                         ▼
 ┌───────────────────────────────────────────────────────────────────────────────┐
 │                       CANONICAL GRAPH QUERY CLIENT                            │
 │   - GET /api/v1/graph/overview (Global backbone)                              │
 │   - GET /api/v1/entities/{id}/neighborhood?depth=N&filter=... (Local expansion)│
 │   - POST /api/v1/graph/query (Advanced topological & attribute query)         │
 └───────────────────────────────────────┬───────────────────────────────────────┘
                                         │
                                         ▼
 ┌───────────────────────────────────────────────────────────────────────────────┐
 │                          PUB NEURAL BACKEND API                               │
 │   - Postgres Read-Only Pools with RLS (Role & Trust Zone enforcement)         │
 │   - CTE Traversal on neural_edges & neural_nodes                              │
 │   - Grounded Evidence resolution on neural_evidence & source_blobs            │
 └───────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Contrato de API (Backend ↔ Graph Explorer)

Para atender tanto ao **Global Graph** quanto à **Expansão Incremental** sem degradar latência ou violar limites de memória:

### 7.1 GET `/api/v1/graph/backbone`
Retorna a malha de nós de nível superior da holding (Projetos, Repositórios, Decisões Ratificadas e Regras Centrais).
- **Query Params:**
  - `trust_zone` (opcional): Filtro de zona de segurança (default: zona da sessão).
  - `limit` (opcional): Padrão 100, máx 250 nós.
- **Resposta:** `GraphResponseDTO` com os nós troncos e suas arestas diretas.

### 7.2 GET `/api/v1/entities/{id}/neighborhood`
Expansão progressiva centrada em um nó alvo.
- **Query Params:**
  - `depth`: Inteiro entre `1` e `2` (default `1`).
  - `limit`: Inteiro entre `1` e `100` (default `50`).
  - `entity_types` (opcional): Lista separada por vírgula para filtrar tipos de vizinhos.
  - `relation_types` (opcional): Lista separada por vírgula para filtrar tipos de arestas.
  - `epistemic_state` (opcional): `CONFIRMED` | `PROPOSED` | `ALL`.
- **Resposta:**
```json
{
  "center_node_id": "decision:pub-ecom:auth-strategy",
  "hop_depth": 1,
  "nodes": [
    {
      "id": "decision:pub-ecom:auth-strategy",
      "entity_type": "DECISION",
      "title": "Supabase SSR Session Tokens",
      "slug": "decision-pub-ecom-auth-strategy",
      "summary": "Architecture for SSR token refresh",
      "promotion_state": "VALIDATED",
      "conflict_state": "RESOLVED",
      "confidence_score": 0.95,
      "valid_from": "2026-09-12T00:00:00Z",
      "valid_until": null,
      "trust_zone": "tz_internal_holding",
      "project_id": "pub-ecom",
      "evidence_count": 4,
      "degree": 5
    }
  ],
  "edges": [
    {
      "id": "3e234a60-...",
      "source_id": "decision:pub-ecom:auth-strategy",
      "target_id": "rule:pub-core:zero-mutation",
      "relation_type": "IMPLEMENTS",
      "weight": 0.95,
      "is_bidirectional": false,
      "trust_zone": "tz_internal_holding",
      "is_active": true,
      "association_status": "CONFIRMED",
      "provenance": {
        "extractor": "graphify-v8",
        "confidence": 0.95,
        "epistemic_classification": "EXTRACTED"
      }
    }
  ],
  "total_nodes": 6,
  "total_edges": 5
}
```

---

## 8. Modelagem Visual de Entidades e Relações

### 8.1 Nós (Nodes)
Os nós deixam de ser caixas retangulares opacas e passam a ter representação em dois níveis (Level of Detail - LOD):
- **LOD 0 (Zoom Geral / Constelação):** Círculo estilizado com anel de cor por `entity_type`, raio determinado pela métrica $R = \text{clamp}(8 + \sqrt{\text{degree}} \times 3, 8, 32)$ px, com brilho (glow) para nós em foco.
- **LOD 1 (Zoom Médio):** Círculo com ícone do tipo de entidade e label flutuante abaixo com tipografia compacta mono/sans.
- **LOD 2 (Zoom Próximo / Foco):** Cartão contextual completo com título, status epistemológico e tags de projeto.

#### Paleta Canônica de Cores (Semantic Theme):
- `DECISION`: Roxo Elétrico (`#8b5cf6` / `#1f1b2e`)
- `RULE`: Âmbar / Ouro (`#f59e0b` / `#2a1e12`)
- `PATTERN`: Ciano / Menta (`#06b6d4` / `#112629`)
- `LESSON`: Verde Esmeralda (`#10b981` / `#13271d`)
- `PROJECT`: Azul Real (`#3b82f6` / `#142136`)
- `REPOSITORY`: Cinza Titânio (`#64748b` / `#1b212b`)
- `EVIDENCE`: Azul Céu Profundo (`#0284c7` / `#122333`)
- `CONCEPT`: Violeta Místico (`#a855f7` / `#221933`)

### 8.2 Arestas (Edges)
- **Direção:** Linhas curvas Bezier ou retas suaves com seta indicativa no nó alvo.
- **Peso/Espessura:** Proporcional ao `weight` da relação ($1.0$ a $3.5$ px).
- **Estilo por Epistemic State:**
  - `EXTRACTED` / Factual (AST, código): Linha contínua sólida e luminosa.
  - `INFERRED` / Heurístico (co-ocorrência): Linha tracejada (`stroke-dasharray: 4, 4`) com opacidade calibrada a 0.65.
  - `CONTRADICTS`: Linha vermelha pulsante (`#ef4444`) com indicador de conflito.

---

## 9. Estratégia para Grafos em Grande Escala (Large Graph Strategy)

Um dos maiores desafios de visualização de grafos é evitar o "novelo de lã" ininteligível (hairball graph) e travamento de DOM ao ultrapassar centenas de elementos:

```text
                          GRAPHS ESCALABILITY PILLARS
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
  1. LAZY LOADING              2. LEVEL OF DETAIL             3. FORCE TUNING
  (Neighborhood CTE)             (Canvas / SVG Culling)         (Barnes-Hut / Quadtree)
```

1. **Neighborhood Expansion (On-Demand Loading):**
   - O browser **nunca** faz download da tabela inteira `neural_nodes`.
   - Inicialização com o esqueleto do grafo (máx 50-100 nós principais).
   - Expansão ocorre ao clicar duas vezes em um nó ou pressionar a tecla `E` (Expand), trazendo até 25 novos vizinhos incrementais via API e fundindo ao estado local sem recalcular posições dos nós já fixados.
2. **Viewport Culling (Otimização de Renderização):**
   - Elementos fora da bounding box da janela de visualização atual são omitidos do pipeline de repintura do Canvas/SVG.
3. **Simulação por Quadtree (Barnes-Hut Approximation):**
   - O algoritmo de física de forças agrupa aglomerados distantes em centros de massa únicos, reduzindo o custo computacional de $O(N^2)$ para $O(N \log N)$.
4. **Agrupamento por Comunidades (Community Collapsing):**
   - Repositórios com centenas de funções e métodos menores são agregados visualmente em nós virtuais de submódulos/comunidades (`COMMUNITY_BELONGS_TO`), permitindo abrir e fechar clusters com um clique.

---

## 10. Integração com o Research Runtime

O Graph Explorer funciona como a interface de investigação do ciclo de pesquisa do PUB Neural:

```text
Research Question
       ↓
Research Run
       ↓
Sources & Evidence
       ↓
Extraction (Graphify)
       ↓
Canonical Graph
       ↓
GRAPH EXPLORER (Exploração Visual e Descoberta de Padrões)
       ↓
Cross-comparison (Divergências e Contradições)
       ↓
Synthesis & Findings
       ↓
CEO Sovereign Ratification
```

### Casos de Uso Bidirecionais:
- **Do Grafo para o Código:** O operador clica no nó de uma `RULE`, inspeciona suas `EVIDENCE` no painel lateral, visualiza o snippet com número de linha e clica para abrir o arquivo fonte verificado no repositório.
- **Da Pergunta de Pesquisa para o Grafo:** Ao executar uma query de pesquisa (ex: *"Quais serviços dependem do Supabase SSR?"), o resultado ranqueado pelo 3-Way RRF destaca os nós vencedores diretamente no Graph Explorer, traçando o caminho mínimo (Shortest Path) entre as entidades investigadas.

---

## 11. Decisão Técnica: Seleção da Biblioteca de Visualização

### Análise Comparativa de Tecnologias

| Critério | React Flow (`@xyflow/react`) Atual | Cytoscape.js | D3-Force + SVG/Canvas | React Force Graph (`force-graph`) |
| :--- | :--- | :--- | :--- | :--- |
| **Paradigma Principal** | Node-based workflows / Caixas DOM | Análise de redes & bioinformática | Primitivas matemáticas customizadas | Visualização interativa force-directed |
| **Sensação Obsidian** | Baixa (orientado a caixas rígidas) | Média (requer muita estilização) | Altíssima (flexibilidade total) | **Máxima (Idêntica ao Obsidian)** |
| **Performance (> 500 nós)**| Sofre com DOM nodes | Boa (Canvas nativo) | Altíssima (Canvas/WebGL) | **Altíssima (Canvas 2D / Three.js WebGL)** |
| **Física Force-Directed** | Limitada / Requer plugin externo | Embutida (CoSE, fcose) | Embutida (`d3-force`) | **Embutida e nativamente calibrada** |
| **Curva de Integração** | Já instalado | Média | Alta (baixo nível) | **Baixa/Média (Componente React pronto)** |
| **Manutenibilidade** | Alta no projeto atual | Média | Complexa | **Excelente (TypeScript nativo, Canvas performático)** |

### Recomendação Final
- **Opção Recomendada:** **`react-force-graph-2d`** (ou `force-graph` encapsulado em componente React).
- **Por quê?**
  1. Fornece exatamente a experiência espacial, inércia, partículas e física de molas do **Obsidian Graph View**.
  2. Suporta renderização em **HTML5 Canvas**, permitindo manipular de 100 a 5.000 nós e arestas com 60 FPS estáveis, impossível de alcançar com nós baseados em elementos DOM comuns.
  3. Preserva a capacidade de customizar renderizadores de nós (LOD com anéis semânticos, cores por `entity_type` e ícones).
  4. Mantém React Flow reservado caso seja necessário construir no futuro editores visuais de pipeline ou fluxogramas rígidos de dados.

---

## 12. Matriz de Reutilização vs Reconstrução

| Componente | Origem | Ação | Justificativa Técnica |
| :--- | :--- | :--- | :--- |
| **Paleta Semântica de Cores** | `EntityNode.tsx` do Neural | **Reutilizar** | A codificação de cores por `entity_type` (roxo, âmbar, ciano, esmeralda) já está perfeitamente alinhada à ontologia canônica. |
| **Algoritmo de Modularidade / Comunidades**| Graphify (`Louvain`) | **Reutilizar Conceito**| A detecção de comunidades modulares é ideal para colorir clusters estruturais no grafo do Neural. |
| **Parser e Sanitizador JSON** | `GraphifyAdapter` | **Reutilizar** | Já testado e protegido contra injection, secrets vazados e estouro de nós. |
| **Renderizador Canvas Force-Directed** | Obsidian Inspiration | **Reconstruir Nativo** | O atual Dagre em React Flow deve ser substituído por um canvas force-directed orgânico (`react-force-graph`). |
| **Painéis Laterais (Inspector)** | `InspectorPanel.tsx` do Neural | **Adaptar / Evoluir** | O painel lateral existente já detalha entidades e evidências; basta estender para suportar inspeção de arestas (`EdgeInspector`). |
| **Backend Query Engine** | `graph_service.py` do Neural | **Evoluir** | Adicionar rota de backbone e filtros dinâmicos por tipo de entidade/relação à CTE recursiva existente. |

---

## 13. Plano de Implementação Progressivo (3 Passos)

1. **Passo 1 (Backend Query Hardening):**
   - Evoluir `console/backend/services/graph_service.py` para incluir o endpoint `/api/v1/graph/backbone` (esqueleto global de projetos e regras) e suporte a filtros por tipo de entidade e relação.
2. **Passo 2 (Force Canvas Engine):**
   - Integrar `react-force-graph-2d` ao frontend do console, implementando simulação de força calibrada, Level of Detail (LOD) e renderização personalizada dos anéis semânticos.
3. **Passo 3 (Inspector & Interactive Controls):**
   - Conectar clique duplo para expansão incremental de vizinhos, foco de hover, Edge Inspector e barra de filtros em tempo real vinculada ao estado do grafo.

---

## 14. Riscos & Mitigações

- **Risco de Travamento por Sobrecarga de Dados:** Queries irrestritas podem tentar renderizar 10.000 nós de código de uma vez.
  - *Mitigação:* Limite defensivo rígido no backend (`bounded_limit = max(1, min(limit, 150))`) e expansão progressiva sob demanda.
- **Risco de Conflito de Licença:** O Graphify é Apache-2.0.
  - *Mitigação:* Nenhuma linha de código proprietário fechado é copiada sem atribuição; as ideias de visualização de grafos e física de forças baseiam-se em algoritmos de domínio público (`d3-force`, Barnes-Hut).
- **Risco de Conflito com a Ontologia Canônica:** A visualização tentar inventar tipos de nós não suportados.
  - *Mitigação:* Tipos e estados obedecem estritamente aos enums fechados do PostgreSQL (`neural_entity_type`, `neural_relation_type`, `neural_promotion_state`).

---

## 15. Perguntas Abertas para Futuras Fases

1. Desejamos permitir alternar entre a visão orgânica Force-Directed (estilo Obsidian) e a visão hierárquica em árvore (estilo Dagre/React Flow) através de um seletor na barra de ferramentas?
2. Devemos persistir as coordenadas cartesianas $(X, Y)$ ajustadas manualmente pelo usuário no banco de dados para que a visualização de um projeto permaneça estável entre sessões?
