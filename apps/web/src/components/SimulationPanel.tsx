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
  timestamp?: string;
  target?: string;
  port?: number;
  state?: string;
  banner?: string;
  dst_port?: number;
  src_ip?: string;
  dst_ip?: string;
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

type MLResultEntry = {
  input?: ScanRow;
  ml?: {
    is_port_probe?: boolean;
    is_dos?: boolean;
    confidence?: number;
  };
  error?: string;
  average_confidence?: number;
  note?: string;
  target?: string;
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
  const isSupported = attackType === "Port Probing" || attackType === "DOS";

  const runSimulation = async () => {
    if (!isSupported) {
      setError("Not yet implemented: only Port Probing and DOS are available from bundled simulations.");
      return;
    }

    setRunning(true);
    setStatusMessage(`Sending ${requestCount} request(s) to backend...`);
    setError(null);
    setScenarios([]);
    setExpandedPayload(new Set());
    setExpandedResponse(new Set());

    try {
      const runResp = await fetch(`${API_BASE_URL}/run-attack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attack: activeAttack?.runName || "Port Probing",
          requestCount,
          max_age_seconds: attackType === "Port Probing" ? 300 : undefined,
        }),
      });
      if (!runResp.ok) {
        throw new Error(`run-attack responded with ${runResp.status}`);
      }
      const body = await runResp.json();
      const resultsArray: MLResultEntry[] = Array.isArray(body?.results)
        ? (body.results as MLResultEntry[])
        : [];

      let results: ScenarioResult[] = [];
      if (attackType === "DOS") {
        const avgConf =
          typeof body?.average_confidence === "number" ? body.average_confidence : null;
        const payload = Array.isArray(body?.payload) ? (body.payload as ScanRow[]) : [];
        const response = {
          average_confidence: avgConf,
          note: body?.note,
          target: body?.target,
        };
        results = [
          {
            requestId: 1,
            payload: payload,
            response,
            verdict: avgConf !== null ? avgConf >= 0.5 : false,
            confidence: avgConf,
            message: body?.note && body.note !== "DoS simulation completed." ? body.note : undefined,
          },
        ];
      } else {
        const payload = Array.isArray(body?.payload) ? (body.payload as ScanRow[]) : [];
        const confidences = resultsArray
          .map((entry) => (typeof entry?.ml?.confidence === "number" ? entry.ml.confidence : null))
          .filter((n): n is number => n !== null);
        const avgConf =
          confidences.length > 0
            ? confidences.reduce((acc, n) => acc + n, 0) / confidences.length
            : null;
        const positives = resultsArray.filter((entry) => entry?.ml?.is_port_probe).length;
        const verdict =
          avgConf !== null ? avgConf >= 0.5 : positives > resultsArray.length / 2;
        const firstError = resultsArray.find((entry) => entry?.error)?.error;

        results = [
          {
            requestId: 1,
            payload,
            response: {
              average_confidence: avgConf,
              positives,
              total: resultsArray.length,
            },
            verdict,
            confidence: avgConf,
            message: firstError,
            error: firstError,
          },
        ];
      }

      setScenarios(results);
      setStatusMessage(null);
    } catch (err) {
      console.error("simulation request failed:", err);
      setError(err instanceof Error ? err.message : "Request failed");
      setStatusMessage(null);
    }

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
            {attackType === "DOS" ? (
              <>
                <option value={1000}>1k requests</option>
                <option value={2000}>2k requests</option>
                <option value={5000}>5k requests</option>
              </>
            ) : (
              <>
                <option value={100}>100 requests</option>
                <option value={1000}>1k requests</option>
                <option value={5000}>5k requests</option>
              </>
            )}
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
          Not yet implemented: only Port Probing and DOS can be triggered from available simulations.
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
              ML Decisions ({scenarios.length} response{scenarios.length === 1 ? "" : "s"})
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
                    Response #{scenario.requestId}: Attack detected:{" "}
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
