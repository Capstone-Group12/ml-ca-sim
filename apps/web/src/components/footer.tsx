import Link from "next/link";

export default function Footer() {
  return (
    <footer className="mt-10 border-t border-white/10 bg-slate-950/80 py-6 text-sm text-slate-200 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4">
        <span className="font-semibold">Capstone Group 12</span>
        <Link
          href="/about"
          className="rounded-md border border-white/10 px-3 py-1 text-slate-100 transition hover:border-white/30 hover:bg-white/5"
        >
          Meet the Team
        </Link>
      </div>
    </footer>
  );
}
