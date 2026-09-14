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

  const handleSelectEvent = (eventId: string) => {
    console.info(`[Timeline Hook] Selected event: ${eventId} (Timeline surface planned for Phase 3)`);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", width: "100vw", overflow: "hidden", backgroundColor: "#0f172a" }}>
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left Pane: Explorer */}
        <div style={{ width: 320, flexShrink: 0 }}>
          <ExplorerSidebar
            onSelectEntity={handleSelectEntity}
            selectedEntityId={selectedEntityId}
          />
        </div>

        {/* Center Pane: Interactive Knowledge Graph */}
        <div style={{ flex: 1, position: "relative" }}>
          <GraphCanvas
            entityId={selectedEntityId}
            onNodeSelect={handleSelectEntity}
          />
        </div>

        {/* Right Pane: Deep Inspector */}
        <div style={{ width: 380, flexShrink: 0 }}>
          <InspectorPanel
            entityId={selectedEntityId}
            onNavigateEntity={handleSelectEntity}
            onSelectEvent={handleSelectEvent}
          />
        </div>
      </div>

      {/* Bottom: Status Bar */}
      <StatusBar />
    </div>
  );
}

export default App;
