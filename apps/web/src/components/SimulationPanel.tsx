'use client';

import React from "react";
import AttackSelector, { AttackType } from "./AttackSelector";
import sampleScan from "../data/port_probe_fallback.json";

const SUPPORTED_ATTACKS: Record<
  AttackType,
  { runName: string; getSample: () => ScanRow[], requestCount?: number }
> = {
  "Port Probing": {
    runName: "Port Probing",
    getSample: () =>
      (sampleScan as ScanRow[]).map((row) => ({
        ...row,
        banner: row.banner || "Port Probing simulated",
      })),
    requestCount: 100,
  },
  DOS: {
    runName: "DOS",
    getSample: () => [],
  },
  "XSS/SQL Injection": {
    runName: "XSS/SQL Injection",
    getSample: () => [],
  },
  "Brute Force": {
    runName: "Brute Force",
    getSample: () => [],
  },
  Slowloris: {
    runName: "Slowloris",
    getSample: () => [],
  },
};

type ScanRow = {
  timestamp: string;
  target: string;
  port: number;
  state: string;
  banner: string;
};

type ScenarioResult = {
  requestId: number;
  payload: ScanRow[];
  response: unknown;
  verdict: boolean;
  confidence: number | null;
  message?: string;
  error?: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "https://mlcasim-api.edwardnafornita.com";

const palette = {
  panel: "bg-slate-900/80",
  border: "border-white/10",
  text: "text-white",
};

export default function SimulationPanel() {
  const [attackType, setAttackType] = React.useState<AttackType>("Port Probing");
  const [statusMessage, setStatusMessage] = React.useState<string | null>(null);
  const [scenarios, setScenarios] = React.useState<ScenarioResult[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [expandedPayload, setExpandedPayload] = React.useState<Set<number>>(new Set());
  const [expandedResponse, setExpandedResponse] = React.useState<Set<number>>(new Set());
  const [requestCount, setRequestCount] = React.useState<number>(100);
  const [running, setRunning] = React.useState(false);

  const activeAttack = SUPPORTED_ATTACKS[attackType];
  const isSupported = Boolean(activeAttack && activeAttack.runName === "Port Probing");

  const fetchPayloadRows = React.useCallback(async (): Promise<ScanRow[]> => {
    try {
      const runResp = await fetch(`${API_BASE_URL}/run-attack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attack: activeAttack?.runName || "Port Probing",
          requestCount,
          max_age_seconds: 300,
        }),
      });
      if (!runResp.ok) {
        throw new Error(`run-attack responded with ${runResp.status}`);
      }
      const runBody = await runResp.json();
      const candidate = Array.isArray(runBody?.payload) ? runBody.payload : null;
      if (candidate && candidate.length) {
        return candidate as ScanRow[];
      }
    } catch (err) {
      console.error("run-attack failed, falling back to local payload:", err);
    }
    const fallback = activeAttack?.getSample() || [];
    if (!fallback.length) {
      throw new Error("No payload rows available to send");
    }
    return fallback;
  }, [activeAttack, requestCount]);

  const runSimulation = async () => {
    if (!isSupported) {
      setError("Not yet implemented: only Port Probing is available from bundled simulations.");
      return;
    }

    setRunning(true);
    setStatusMessage(`Sending ${requestCount} request(s) to backend...`);
    setError(null);
    setScenarios([]);
    setExpandedPayload(new Set());
    setExpandedResponse(new Set());

    let payloadRows: ScanRow[];
    try {
      payloadRows = await fetchPayloadRows();
    } catch (err) {
      setRunning(false);
      setError(err instanceof Error ? err.message : "Failed to load payload");
      setStatusMessage(null);
      return;
    }

    const results: ScenarioResult[] = [];
    for (let i = 0; i < requestCount; i += 1) {
      try {
        const filteredPayload = [payloadRows[i % payloadRows.length]];
        const predictResp = await fetch(`${API_BASE_URL}/predict-from-scan-json`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(filteredPayload),
        });
        if (!predictResp.ok) {
          throw new Error(`predict-from-scan-json responded with ${predictResp.status}`);
        }
        const body = await predictResp.json();
        const resultsArray = Array.isArray(body?.results) ? body.results : [];
        const firstResult = resultsArray[0] ?? null;

        const ml = firstResult?.ml as
          | { is_port_probe?: boolean; confidence?: number }
          | undefined;

        const verdict = Boolean(ml?.is_port_probe);
        const confidence = typeof ml?.confidence === "number" ? ml.confidence : null;

        const res: ScenarioResult = {
          requestId: i + 1,
          payload: filteredPayload,
          response: firstResult ?? body,
          verdict,
          confidence,
          message: firstResult?.error,
        };
        results.push({ ...res, requestId: i + 1 });
      } catch (err) {
        console.error("simulation request failed:", err);
        results.push({
          requestId: i + 1,
          payload: [payloadRows[i % payloadRows.length]],
          response: null,
          verdict: false,
          confidence: null,
          error: err instanceof Error ? err.message : "Request failed",
        });
      }
    }

    setScenarios(results);
    setStatusMessage(null);
    setRunning(false);
  };

  return (
    <section
      className={`w-full max-w-5xl rounded-xl ${palette.panel} p-6 shadow-2xl ring-1 ring-white/10 backdrop-blur`}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <AttackSelector value={attackType} onChange={(v) => setAttackType(v)} />

        <div className="flex flex-col gap-1">
          <label htmlFor="request-count" className="text-sm font-medium text-gray-100">
            Requests
          </label>
          <select
            id="request-count"
            value={requestCount}
            onChange={(e) => setRequestCount(Number(e.target.value))}
            disabled={running}
            className="w-40 rounded-md border border-white/20 bg-white/10 px-3 py-2 text-white shadow-inner focus:border-white focus:outline-none focus:ring-1 focus:ring-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            <option value={100}>100 requests</option>
            <option value={1000}>1k requests</option>
            <option value={5000}>5k requests</option>
          </select>
        </div>

        <button
          onClick={runSimulation}
          disabled={running || !isSupported}
          className="inline-flex items-center justify-center rounded-md bg-white px-4 py-2 text-sm font-semibold text-slate-900 shadow transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {running ? "Running..." : "Run Simulation"}
        </button>
      </div>

      {!isSupported && (
        <div className="mt-3 rounded-md border border-amber-400/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          Not yet implemented: only Port Probing can be triggered from available simulations.
        </div>
      )}

      {statusMessage && (
        <div className="mt-4 rounded-md border border-white/10 bg-slate-800/80 px-4 py-3 text-sm text-slate-100">
          {statusMessage}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-md border border-red-400/40 bg-red-500/10 px-4 py-3 text-sm text-red-100">
          {error}
        </div>
      )}

      {scenarios.length > 0 && (
        <div className="mt-5 rounded-lg border border-white/10 bg-slate-900/70 p-4 shadow-inner">
          <div className="mb-3">
            <h2 className="text-xl font-semibold text-white">
              ML Decisions ({scenarios.length} request{scenarios.length === 1 ? "" : "s"})
            </h2>
            <p className="text-sm text-slate-300">
              Each entry shows the single payload sent and the corresponding response.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            {scenarios.map((scenario) => (
              <div
                key={scenario.requestId}
                className={`rounded-md border ${palette.border} bg-slate-800/60 p-4 shadow-sm text-left`}
              >
                <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                  <div className="text-sm font-semibold text-white">
                    Request #{scenario.requestId}: Attack detected:{" "}
                    <span className={scenario.verdict ? "text-emerald-300" : "text-red-400"}>
                      {scenario.verdict ? "True" : "False"}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300">
                    Confidence:{" "}
                    {scenario.confidence !== null
                      ? `${(scenario.confidence * 100).toFixed(1)}%`
                      : "Not provided"}
                  </div>
                </div>

                {scenario.message && (
                  <div className="mt-2 rounded border border-amber-400/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
                    Backend reported: {scenario.message}
                  </div>
                )}

                {scenario.error && (
                  <div className="mt-2 rounded border border-red-400/40 bg-red-500/10 px-3 py-2 text-xs text-red-100">
                    {scenario.error}
                  </div>
                )}

                <div className="my-2 h-px bg-white/10" />

                <div className="flex flex-wrap gap-2">
                  <button
                    className="rounded border border-white/20 px-3 py-1 text-xs font-semibold text-white hover:bg-white/10"
                    onClick={() =>
                      setExpandedPayload((prev) => {
                        const next = new Set(prev);
                        if (next.has(scenario.requestId)) {
                          next.delete(scenario.requestId);
                        } else {
                          next.add(scenario.requestId);
                        }
                        return next;
                      })
                    }
                  >
                    {expandedPayload.has(scenario.requestId) ? "Hide Input JSON" : "Show Input JSON"}
                  </button>
                  <button
                    className="rounded border border-white/20 px-3 py-1 text-xs font-semibold text-white hover:bg-white/10"
                    onClick={() =>
                      setExpandedResponse((prev) => {
                        const next = new Set(prev);
                        if (next.has(scenario.requestId)) {
                          next.delete(scenario.requestId);
                        } else {
                          next.add(scenario.requestId);
                        }
                        return next;
                      })
                    }
                  >
                    {expandedResponse.has(scenario.requestId) ? "Hide Output JSON" : "Show Output JSON"}
                  </button>
                </div>

                {expandedPayload.has(scenario.requestId) && (
                  <pre className="mt-2 rounded border border-white/10 bg-[#1e1e2e] p-4 font-mono text-sm leading-relaxed text-[#f2f5f7] whitespace-pre-wrap break-words">
                    {JSON.stringify(scenario.payload, null, 2)}
                  </pre>
                )}

                {expandedResponse.has(scenario.requestId) && (
                  <pre className="mt-2 rounded border border-white/10 bg-[#1e1e2e] p-4 font-mono text-sm leading-relaxed text-[#f2f5f7] whitespace-pre-wrap break-words">
                    {JSON.stringify(scenario.response, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
