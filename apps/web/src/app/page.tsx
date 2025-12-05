import Link from "next/link";
import SimulationPanel from "@/components/SimulationPanel";

export default function Home() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 py-10 text-center text-white">
      <div>
        <h1 className="text-4xl font-semibold">Cyberattack Simulation</h1>
        <p className="mt-2 text-slate-200">
          Launch port probing samples and inspect how the ML model classifies traffic.
        </p>
        <Link
          href="/flow"
          className="mt-3 inline-flex items-center rounded-md border border-white/10 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:border-white/30 hover:bg-white/5"
        >
          See system flow diagram
        </Link>
      </div>

      <div className="flex w-full justify-center">
        <SimulationPanel />
      </div>
    </div>
  );
}
