import os

def fix_imports(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('import { Node, Edge }', 'import type { Node, Edge }')
    content = content.replace('import {\n  GraphResponseDTO,\n  EntityDetailDTO,\n  SearchResponseDTO,\n  SystemStatusDTO,\n} from "./types";', 'import type { GraphResponseDTO, EntityDetailDTO, SearchResponseDTO, SystemStatusDTO } from "./types";')
    content = content.replace('import { SearchResultItemDTO } from "../api/types";', 'import type { SearchResultItemDTO } from "../api/types";')
    content = content.replace('import { EntityDetailDTO } from "../api/types";', 'import type { EntityDetailDTO } from "../api/types";')
    content = content.replace('import { SystemStatusDTO } from "../api/types";', 'import type { SystemStatusDTO } from "../api/types";')
    content = content.replace('  Node,\n  Edge,\n}', '  type Node,\n  type Edge,\n}')
    content = content.replace("import { GraphNodeDTO, GraphEdgeDTO } from '../api/types';", "import type { GraphNodeDTO, GraphEdgeDTO } from '../api/types';")
    content = content.replace('import { GraphNodeDTO, GraphEdgeDTO, GraphResponseDTO } from "../api/types";', 'import type { GraphNodeDTO, GraphEdgeDTO, GraphResponseDTO } from "../api/types";')
    content = content.replace('data: edge,', 'data: edge as unknown as Record<string, unknown>,')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.ts') or file.endswith('.tsx'):
            fix_imports(os.path.join(root, file))
