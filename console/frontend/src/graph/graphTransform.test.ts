import { describe, it, expect } from 'vitest';
import { transformNodes, transformEdges } from './graphTransform';
import type { GraphNodeDTO, GraphEdgeDTO } from '../api/types';

describe('graphTransform', () => {
  it('transforms nodes correctly', () => {
    const dtoNodes: GraphNodeDTO[] = [
      {
        id: 'node-1',
        entity_type: 'PROJECT',
        title: 'Project 1',
        slug: 'project-1',
        summary: null,
        promotion_state: 'DRAFT',
        conflict_state: 'NONE',
        confidence_score: 1.0,
        valid_from: '2023-01-01',
        valid_until: null,
        trust_zone: 'PUBLIC',
        project_id: null,
        evidence_count: 0
      }
    ];

    const nodes = transformNodes(dtoNodes, 'node-1');
    expect(nodes.length).toBe(1);
    expect(nodes[0].id).toBe('node-1');
    expect(nodes[0].data.label).toBe('Project 1');
    expect(nodes[0].data.isCenter).toBe(true);
  });

  it('transforms edges correctly', () => {
    const dtoEdges: GraphEdgeDTO[] = [
      {
        id: 'edge-1',
        source_id: 'node-1',
        target_id: 'node-2',
        relation_type: 'DEPENDS_ON',
        weight: 1.0,
        is_bidirectional: false,
        trust_zone: 'PUBLIC',
        is_active: true
      }
    ];

    const edges = transformEdges(dtoEdges);
    expect(edges.length).toBe(1);
    expect(edges[0].id).toBe('edge-1');
    expect(edges[0].source).toBe('node-1');
    expect(edges[0].target).toBe('node-2');
    expect(edges[0].animated).toBe(true);
  });
});
