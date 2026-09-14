import { useState } from "react";
import { ExplorerSidebar } from "./components/ExplorerSidebar";
import { InspectorPanel } from "./components/InspectorPanel";
import { GraphCanvas } from "./graph/GraphCanvas";
import { StatusBar } from "./components/StatusBar";

function App() {
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);

  const handleSelectEntity = (id: string) => {
    setSelectedEntityId(id);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ width: 300, flexShrink: 0 }}>
          <ExplorerSidebar onSelectEntity={handleSelectEntity} />
        </div>
        <div style={{ flex: 1, position: 'relative' }}>
          <GraphCanvas entityId={selectedEntityId} onNodeClick={handleSelectEntity} />
        </div>
        <div style={{ width: 350, flexShrink: 0 }}>
          <InspectorPanel entityId={selectedEntityId} />
        </div>
      </div>
      <StatusBar />
    </div>
  );
}

export default App;
