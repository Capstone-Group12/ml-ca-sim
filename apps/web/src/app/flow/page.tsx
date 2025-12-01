const diagram = `
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant MLService
    participant Prometheus

    User->>Frontend: Choose "Port Probing" + Run
    Frontend->>API: POST /predict-from-scan-json (scan JSON)
    API->>MLService: POST /predict (features)
    MLService-->>API: Prediction + confidence
    API-->>Frontend: Cleaned result
    Frontend-->>User: Verdict + JSON
    Prometheus-->>API: Scrapes /metrics (observability)
`;

export default function FlowPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 text-white">
      <h1 className="text-3xl font-semibold text-center">System Flow</h1>
      <p className="mt-3 text-center text-slate-200">
        How traffic moves from the browser to the ML service and back.
      </p>

      <div className="mt-6 rounded-lg border border-white/10 bg-slate-900/70 p-4 shadow-lg ring-1 ring-white/10">
        <pre className="overflow-auto rounded bg-[#1e1e2e] p-4 text-sm text-sky-100">{diagram}</pre>
      </div>

      <div className="mt-6 flex justify-center">
        <a
          href="/"
          className="inline-flex items-center rounded-md border border-white/20 px-4 py-2 text-sm font-semibold text-white transition hover:border-white/40 hover:bg-white/10"
        >
          Back to Simulator
        </a>
      </div>
    </div>
  );
}
