import { useState } from "react";
import { ExplorerSidebar } from "./components/ExplorerSidebar";
import { InspectorPanel } from "./components/InspectorPanel";
import { GraphCanvas } from "./graph/GraphCanvas";
import { TimelineView } from "./timeline/TimelineView";
import { SystemStatusBar } from "./components/SystemStatusBar";

function App() {
  const [viewMode, setViewMode] = useState<"graph" | "timeline">("graph");
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [inspectorTab, setInspectorTab] = useState<"entity" | "event">("entity");

  // Selection handlers
  const handleSelectEntity = (id: string) => {
    setSelectedEntityId(id);
    setInspectorTab("entity");
    setViewMode("graph");
  };

  const handleSelectEvent = (eventId: string) => {
    setSelectedEventId(eventId);
    setInspectorTab("event");
  };

  const handleOriginatingEventFromEntity = (eventId: string) => {
    setSelectedEventId(eventId);
    setInspectorTab("event");
    setViewMode("timeline");
  };

  const handleNavigateEntityFromEvent = (entityId: string) => {
    setSelectedEntityId(entityId);
    setInspectorTab("entity");
    setViewMode("graph");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
        backgroundColor: "#0f172a",
      }}
    >
      {/* 1. TOP BAR / SYSTEM STATUS */}
      <SystemStatusBar viewMode={viewMode} onViewModeChange={setViewMode} />

      {/* 2. THREE-PANE SHELL */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left Pane: Explorer */}
        <div style={{ width: 320, flexShrink: 0 }}>
          <ExplorerSidebar
            onSelectEntity={handleSelectEntity}
            selectedEntityId={selectedEntityId}
          />
        </div>

        {/* Center Pane: Graph or Timeline */}
        <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
          {viewMode === "graph" ? (
            <GraphCanvas
              entityId={selectedEntityId}
              onNodeSelect={handleSelectEntity}
            />
          ) : (
            <TimelineView
              selectedEventId={selectedEventId}
              onSelectEvent={handleSelectEvent}
              onNavigateEntity={handleNavigateEntityFromEvent}
            />
          )}
        </div>

        {/* Right Pane: Deep Inspector (Entity or Event) */}
        <div style={{ width: 380, flexShrink: 0 }}>
          <InspectorPanel
            entityId={selectedEntityId}
            eventId={selectedEventId}
            activeTab={inspectorTab}
            onTabChange={setInspectorTab}
            onNavigateEntity={handleNavigateEntityFromEvent}
            onSelectEvent={handleOriginatingEventFromEntity}
            onCloseEvent={() => {
              setSelectedEventId(null);
              setInspectorTab("entity");
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
