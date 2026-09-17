# PUB DAILY RECORD — 2026-09-16

## Propósito
Registro arquitetural consolidado das decisões e direcionamentos do dia relacionados ao ecossistema PUB Core Holding.

## Research externo do dia
Capacidades pesquisadas e destino canônico:

| Referência | Capacidade absorvida | Dono PUB |
|---|---|---|
| Graphify | knowledge/code graph, relações explícitas vs inferidas, evidência e confiança | PUB Neural |
| PAUL | PLAN → APPLY → UNIFY, acceptance criteria, diagnóstico, reconciliação e estados não-binários | PDL |
| OpenHands | sessões, múltiplos backends, automações, agent server e UX operacional | Control Room / ACP como referência arquitetural |
| Coolify | infraestrutura, deploy, serviços, health, logs, rollback e backup | PUB Machine |
| Maxun | browser-based extraction, scraping, crawling, APIs, scheduling e structured data | PUB Machine → Neural |
| Open WebUI | UX de modelos/agentes, tools, MCP, RAG, automações, observabilidade e permissões | Control Room / laboratório |
| Browser Use | browser agent, navegação, sessões, ferramentas e execução Web | PUB Machine + interface/adaptador ACP |
| Crawl4AI | crawling, normalização, Markdown, structured extraction, RAG ingestion e browser runtime | PUB Machine → Neural |

## Regra arquitetural
**Não importar projetos. Importar capacidades.**

Nenhum desses projetos deve ser transplantado como sistema paralelo. Cada capacidade deve ser implementada ou integrada no projeto PUB que possui a responsabilidade correspondente.

## Arquitetura operacional consolidada

`PDL decide → ACP governa/executa → PUB Machine executa capacidades externas → PUB Neural registra, relaciona e institucionaliza conhecimento → Control Room observa e opera.`

Produtos permanecem independentes e integram por contratos, APIs e eventos. Não compartilhar banco, filesystem, workers ou sessões entre produtos.

## PUB Neural
- Evoluir de memória/RAG para camada cognitiva com observações, evidências, entidades, relações, inferências, confiança e estados temporais.
- Graphify é referência direta para graph/code graph e distinção entre relação extraída e inferida.
- Machine captura/normaliza; Neural armazena, relaciona e aprende.
- Ciclo de conhecimento: `CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED → ADOPTED → INSTITUTIONAL`.

## PDL
- Absorver princípios de PAUL: acceptance criteria, qualification, diagnosis, reconciliation e handoff/resume.
- Estado de tarefa não deve depender apenas de "agente disse que terminou".
- Loop-alvo: `Research → Plan → Execute → Test → Correct → Verify → Learn`.
- Estados relevantes podem incluir `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`.
- PDL decide/plana; ACP não deve absorver sua lógica de planejamento.

## PUB ACP
- ClosedLoopEngine permanece única autoridade de execução.
- Generic ACP permanece isolado/congelado conforme sua governança vigente.
- Browser Use, Crawl4AI, Maxun, OpenHands e Coolify são referências/capabilities externas, não novos executores dentro do ClosedLoopEngine.
- Especialização Web/browser/infrastructure pertence ao PUB Machine; ACP pode expor interfaces/adapters para solicitar essas capacidades.

## Control Room
- É camada de coordenação, operação e observabilidade, não autoridade de execução.
- Deve enxergar o ecossistema PUB, não apenas um subconjunto fixo de projetos.
- OpenHands e Open WebUI servem como referências de UX/agent operations, sem duplicar PDL, ACP ou Neural.
- GitHub é fonte primária para catálogo de projetos/repos; evitar hardcoding.
- Interface operacional deve ser em português.

## PUB Machine
Camada de execução/infrastructure substrate para:
- browser runtime;
- crawling/scraping/extraction;
- sessões e perfis de navegador;
- network/proxy/cache quando necessário;
- structured data acquisition;
- workers e serviços;
- infraestrutura e deployment.

Fluxo recomendado: `captura → normalização → estruturação → PUB Neural`.

## Ordem de implementação orientativa
1. ACP / Control Plane e contratos de execução.
2. PDL e closed loop de engenharia com testes/correção/verificação.
3. PUB Neural e observação/knowledge graph/hybrid retrieval.
4. PUB Machine como substrate de execução Web/dados/infra.
5. Control Room operacional completo sobre todos os projetos.
6. Produtos consumindo essas capacidades por contratos.

A ordem representa dependência operacional e não uma autorização para duplicar arquitetura.

## Evidências GitHub registradas no dia
- `pub-dev-loop`: PR #25, `docs: register external capability allocation`.
- `pub-acp-lab`: PR #1, `docs: register external capability boundaries`.
- `pub-neural`: registro de alocação externa no commit `105ae1e...`.
- `pub-machine`: registro de alocação externa no commit `ffc8b20...`.
- `pub-ops-hub`: registro de alocação externa no commit `905953c...`.
- `PUB-CORE`: registro cross-project no commit `1693949...`.

## Decisões de governança do dia
- PDL não deve ser integrado ao Control Room MVP nesta etapa quando isso alterar a estrutura dependente do AG; primeiro consolidar o Control Room funcional.
- Control Room MVP deve funcionar no navegador e usar dados reais/estado real disponível, sem criar nova arquitetura paralela.
- Generic ACP não deve absorver Control Room, PDL, Neural ou novas responsabilidades de produto.
- Alterações cuja proveniência não esteja resolvida devem permanecer bloqueadas até auditoria apropriada.

## Resultado do dia
O research externo foi transformado de lista de projetos em mapa de capacidades distribuídas. A arquitetura passa a tratar referências externas como fontes de padrões e capacidades especializadas, preservando soberania e fronteiras dos projetos PUB.
