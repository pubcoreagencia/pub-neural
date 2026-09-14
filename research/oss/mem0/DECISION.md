# Architectural Decision: mem0ai/mem0

## Final Decision
```text
DECISION: INSPIRE — memory extraction / agent ergonomics (ARCHITECTURAL REFERENCE)
```

## Concrete Rationale
1. **Code Adoption Rejected:** The OSS storage engine is mutable, unstructured, lacks database-level governance, and does not include graph capabilities. Adopting it would degrade PUB Neural's architectural guarantees.
2. **Architectural Reference Adopted:** Mem0's procedural memory concepts, lightweight agent SDK integration hooks (e.g., automated capture from agent turns), and extraction prompts serve as valuable reference material for designing future PDL client libraries.
