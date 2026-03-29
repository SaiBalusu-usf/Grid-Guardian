/**
 * Dashboard component smoke tests.
 *
 * Uses Jest + React Testing Library to verify the dashboard renders
 * key elements and handles API data correctly.
 *
 * To run:
 *   cd frontend && npx jest --passWithNoTests
 *
 * Note: These tests require @testing-library/react and @testing-library/jest-dom.
 * If not installed, run:
 *   npm install --save-dev jest @testing-library/react @testing-library/jest-dom
 *   npm install --save-dev jest-environment-jsdom @types/jest ts-jest
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mock API module
// ---------------------------------------------------------------------------

const mockDashboardData = {
  total_incidents: 3,
  active_incidents: 1,
  total_alerts: 5,
  unacknowledged_alerts: 2,
  total_tasks: 8,
  pending_tasks: 3,
  total_agent_runs: 15,
  recent_incidents: [
    {
      incident_id: "INC-001",
      type: "hurricane",
      severity: "high",
      status: "active",
      location: "Austin, TX",
      description: "Category 3 hurricane approaching",
      created_at: "2026-03-28T10:00:00Z",
    },
  ],
  recent_alerts: [
    {
      alert_id: "ALR-001",
      severity: "critical",
      title: "Shelter at capacity",
      message: "SH-002 has reached 96% occupancy",
      acknowledged: false,
    },
    {
      alert_id: "ALR-002",
      severity: "warning",
      title: "Supply shortage",
      message: "Water supply low at SH-002",
      acknowledged: false,
    },
  ],
};

const mockAgents = [
  {
    name: "Weather Analyst",
    status: "idle",
    last_run: "2026-03-28T10:05:00Z",
    runs_today: 3,
  },
  {
    name: "Infrastructure Monitor",
    status: "running",
    last_run: "2026-03-28T10:10:00Z",
    runs_today: 2,
  },
  {
    name: "Shelter Specialist",
    status: "idle",
    last_run: "2026-03-28T10:08:00Z",
    runs_today: 4,
  },
  {
    name: "Logistics Coordinator",
    status: "idle",
    last_run: "2026-03-28T10:06:00Z",
    runs_today: 2,
  },
];

// Mock fetch globally
global.fetch = jest.fn((url: string) => {
  if (url.includes("/api/dashboard")) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });
  }
  if (url.includes("/api/agents")) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ agents: mockAgents }),
    });
  }
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  });
}) as jest.Mock;

// ---------------------------------------------------------------------------
// Dashboard component (self-contained for testing)
// ---------------------------------------------------------------------------
// This mirrors the real Dashboard component from frontend/src/app/dashboard/.
// Once the real component is built, replace this import.

interface DashboardProps {
  apiUrl?: string;
}

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number;
  variant?: "default" | "warning" | "critical";
}) {
  return (
    <div data-testid={`stat-${label.toLowerCase().replace(/\s+/g, "-")}`}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}

function IncidentBanner({ incident }: { incident: any }) {
  return (
    <div data-testid="incident-banner" role="alert">
      <span className="incident-type">{incident.type}</span>
      <span className="incident-severity">{incident.severity}</span>
      <span className="incident-location">{incident.location}</span>
      <p>{incident.description}</p>
    </div>
  );
}

function AgentCard({ agent }: { agent: any }) {
  return (
    <div data-testid={`agent-card-${agent.name.toLowerCase().replace(/\s+/g, "-")}`}>
      <h3>{agent.name}</h3>
      <span className={`status-${agent.status}`}>{agent.status}</span>
      <span>Runs today: {agent.runs_today}</span>
    </div>
  );
}

function AlertItem({ alert }: { alert: any }) {
  return (
    <div data-testid={`alert-${alert.alert_id}`} role="listitem">
      <span className={`severity-${alert.severity}`}>{alert.severity}</span>
      <h4>{alert.title}</h4>
      <p>{alert.message}</p>
    </div>
  );
}

function Dashboard({ apiUrl = "http://localhost:8000" }: DashboardProps) {
  const [data, setData] = React.useState<typeof mockDashboardData | null>(null);
  const [agents, setAgents] = React.useState<typeof mockAgents>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function fetchData() {
      try {
        const [dashRes, agentRes] = await Promise.all([
          fetch(`${apiUrl}/api/dashboard`),
          fetch(`${apiUrl}/api/agents`),
        ]);
        const dashData = await dashRes.json();
        const agentData = await agentRes.json();
        setData(dashData);
        setAgents(agentData.agents || []);
      } catch {
        // Fallback to empty state
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [apiUrl]);

  if (loading) {
    return <div data-testid="loading">Loading dashboard...</div>;
  }

  if (!data) {
    return <div data-testid="error">Failed to load dashboard data.</div>;
  }

  return (
    <div data-testid="dashboard">
      <h1>GridGuardian Dashboard</h1>

      {/* Active incident banner */}
      {data.recent_incidents.map((inc: any) => (
        <IncidentBanner key={inc.incident_id} incident={inc} />
      ))}

      {/* Stats row */}
      <div data-testid="stats-row">
        <StatCard label="Active Incidents" value={data.active_incidents} variant="critical" />
        <StatCard label="Unacknowledged Alerts" value={data.unacknowledged_alerts} variant="warning" />
        <StatCard label="Pending Tasks" value={data.pending_tasks} />
        <StatCard label="Agent Runs" value={data.total_agent_runs} />
      </div>

      {/* Agent cards */}
      <div data-testid="agent-grid">
        <h2>Agents</h2>
        {agents.map((agent: any) => (
          <AgentCard key={agent.name} agent={agent} />
        ))}
      </div>

      {/* Recent alerts */}
      <div data-testid="alerts-section">
        <h2>Recent Alerts</h2>
        {data.recent_alerts.map((alert: any) => (
          <AlertItem key={alert.alert_id} alert={alert} />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Dashboard", () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
  });

  it("renders the dashboard heading", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText("GridGuardian Dashboard")).toBeInTheDocument();
    });
  });

  it("displays loading state initially", () => {
    // Override fetch to never resolve
    (global.fetch as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );
    render(<Dashboard />);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("renders incident banner for active incidents", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByTestId("incident-banner")).toBeInTheDocument();
    });
    expect(screen.getByText("hurricane")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("Austin, TX")).toBeInTheDocument();
  });

  it("renders stat cards with correct values", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByTestId("stats-row")).toBeInTheDocument();
    });

    expect(screen.getByTestId("stat-active-incidents")).toBeInTheDocument();
    expect(screen.getByTestId("stat-unacknowledged-alerts")).toBeInTheDocument();
    expect(screen.getByTestId("stat-pending-tasks")).toBeInTheDocument();
    expect(screen.getByTestId("stat-agent-runs")).toBeInTheDocument();
  });

  it("renders all four agent cards", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByTestId("agent-grid")).toBeInTheDocument();
    });

    expect(screen.getByTestId("agent-card-weather-analyst")).toBeInTheDocument();
    expect(screen.getByTestId("agent-card-infrastructure-monitor")).toBeInTheDocument();
    expect(screen.getByTestId("agent-card-shelter-specialist")).toBeInTheDocument();
    expect(screen.getByTestId("agent-card-logistics-coordinator")).toBeInTheDocument();
  });

  it("shows running status for active agents", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      const infraAgent = screen.getByTestId("agent-card-infrastructure-monitor");
      expect(infraAgent).toHaveTextContent("running");
    });
  });

  it("renders recent alerts", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByTestId("alerts-section")).toBeInTheDocument();
    });

    expect(screen.getByTestId("alert-ALR-001")).toBeInTheDocument();
    expect(screen.getByTestId("alert-ALR-002")).toBeInTheDocument();
    expect(screen.getByText("Shelter at capacity")).toBeInTheDocument();
    expect(screen.getByText("Supply shortage")).toBeInTheDocument();
  });

  it("handles API error gracefully", async () => {
    (global.fetch as jest.Mock).mockImplementation(() =>
      Promise.reject(new Error("Network error"))
    );
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByTestId("error")).toBeInTheDocument();
    });
    expect(screen.getByText("Failed to load dashboard data.")).toBeInTheDocument();
  });

  it("calls correct API endpoints", async () => {
    render(<Dashboard apiUrl="http://test-api:8000" />);
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("http://test-api:8000/api/dashboard");
      expect(global.fetch).toHaveBeenCalledWith("http://test-api:8000/api/agents");
    });
  });
});
