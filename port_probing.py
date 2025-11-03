import argparse
import asyncio
import csv
import json
import socket
import sys
from datetime import datetime
from typing import List, Tuple

TARGET = "127.0.0.1"  # endpoint


DEFAULT_COMMON_PORTS = [                                                                # adjust to all portd 1-10000
    20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 110, 111, 123, 135, 137, 138, 139,
    143, 161, 389, 443, 445, 465, 514, 520, 587, 631, 636, 993, 995, 1080, 1433,
    1521, 1723, 2049, 2121, 3306, 3389, 3690, 4444, 4899, 5000, 5060, 5432, 5900,
    6000, 6379, 8080, 8443, 9000, 9090
]


def parse_ports(ports_spec: str) -> List[int]:
    """Parse a port specification string like '22,80,8000-8010'."""
    out = set()
    parts = [p.strip() for p in ports_spec.split(",") if p.strip()]
    for p in parts:
        if "-" in p:
            lo, hi = p.split("-", 1)
            lo = int(lo)
            hi = int(hi)
            if lo < 1 or hi > 65535 or lo > hi:
                raise argparse.ArgumentTypeError(f"Invalid range: {p}")
            out.update(range(lo, hi + 1))
        else:
            port = int(p)
            if port < 1 or port > 65535:
                raise argparse.ArgumentTypeError(f"Invalid port: {p}")
            out.add(port)
    return sorted(out)


async def try_connect(port: int, timeout: float, banner: bool, send_probe: bool, semaphore: asyncio.Semaphore, start_delay: float) -> Tuple[int, str, str]:
    """
    Attempt to connect to TARGET:port.
    Returns (port, state, banner-or-empty).
    state is one of: 'open', 'closed', 'filtered' (timeout/refused)
    """
    if start_delay:
        # slight stagger between starting attempts to reduce burstiness
        await asyncio.sleep(start_delay)

    async with semaphore:
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(TARGET, port), timeout=timeout)
        except (asyncio.TimeoutError, OSError) as e:
            # Timeout -> likely filtered; OSError includes connection refused
            err = str(e).lower()
            if isinstance(e, asyncio.TimeoutError):
                return (port, "filtered", "")
            # If connection refused quickly -> closed
            if "connection refused" in err or "refused" in err:
                return (port, "closed", "")
            # Other network errors treat as filtered
            return (port, "filtered", "")
        # If connected:
        btext = ""
        try:
            if banner:
                # Non-invasive: optionally send a single CRLF (if send_probe True).
                # Many services respond to an empty newline with a banner (SMTP, HTTP, some servers).
                # We do not send any real protocol tokens.
                if send_probe:
                    try:
                        writer.write(b"\r\n")
                        await asyncio.wait_for(writer.drain(), timeout=min(1.0, timeout))
                    except Exception:
                        pass
                # Try to read up to 1024 bytes, but with a small timeout
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=min(1.0, timeout))
                    if data:
                        # decode best-effort
                        try:
                            btext = data.decode("utf-8", errors="replace").strip()
                        except Exception:
                            btext = repr(data[:200])
                except asyncio.TimeoutError:
                    # no banner data in time -> leave empty
                    btext = ""
            # close cleanly
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return (port, "open", btext)
        except Exception:
            try:
                writer.close()
            except Exception:
                pass
            return (port, "open", btext)


async def run_scan(ports: List[int], concurrency: int, timeout: float, banner: bool, send_probe: bool, delay_between_starts: float):
    semaphore = asyncio.Semaphore(concurrency)
    tasks = []
    results = []
    total = len(ports)

    # schedule tasks with slight increasing offset to implement rate control
    for i, port in enumerate(ports):
        start_delay = i * delay_between_starts
        task = asyncio.create_task(try_connect(port, timeout, banner, send_probe, semaphore, start_delay))
        tasks.append(task)

    completed = 0
    for fut in asyncio.as_completed(tasks):
        res = await fut
        results.append(res)
        completed += 1
        # simple progress print
        print(f"[{completed}/{total}] port {res[0]} -> {res[1]}{(' | banner: ' + res[2][:120]) if res[2] else ''}")
    return sorted(results, key=lambda r: r[0])


def write_outputs(results: List[Tuple[int, str, str]], out_prefix: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"{out_prefix}_{ts}.json"
    csv_path = f"{out_prefix}_{ts}.csv"

    data = []
    for port, state, banner in results:
        data.append({
            "timestamp": datetime.now().isoformat(),
            "target": TARGET,
            "port": port,
            "state": state,
            "banner": banner,
        })

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(data, jf, indent=2, ensure_ascii=False)

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=["timestamp", "target", "port", "state", "banner"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    return json_path, csv_path


def print_summary(results: List[Tuple[int, str, str]]):
    open_ports = [p for p, s, b in results if s == "open"]
    closed_ports = [p for p, s, b in results if s == "closed"]
    filtered_ports = [p for p, s, b in results if s == "filtered"]

    print("\nScan summary:")
    print("=============")
    print(f"Target: {TARGET}")
    print(f"Total ports scanned: {len(results)}")
    print(f"Open: {len(open_ports)} -> {open_ports[:20]}")
    print(f"Closed (TCP reset/refused): {len(closed_ports)} -> {closed_ports[:20]}")
    print(f"Filtered/Timeout: {len(filtered_ports)} -> {filtered_ports[:20]}")
    if open_ports:
        print("\nDetected banners (truncated to 200 chars):")
        for p, s, b in results:
            if s == "open" and b:
                print(f" - {p}: {b[:200]}")


def build_argparser():
    p = argparse.ArgumentParser(prog="local_port_prober", description="Async port prober restricted to localhost (127.0.0.1).")
    p.add_argument("--ports", type=str, default=None,
                   help="Comma-separated ports and ranges, e.g. '22,80,8000-8010'. Default: common ports list.")
    p.add_argument("--concurrency", type=int, default=200, help="Maximum concurrent connect attempts (default 200).")
    p.add_argument("--timeout", type=float, default=1.5, help="Connect timeout in seconds (default 1.5).")
    p.add_argument("--banner", action="store_true", help="Attempt to read a banner after connecting (no-send).")
    p.add_argument("--send-probe", action="store_true", help="Send a single CRLF after connect before reading (very light probe).")
    p.add_argument("--delay-between-starts", type=float, default=0.0,
                   help="Stagger start times by this many seconds per port index to limit bursts (default 0).")
    p.add_argument("--out-prefix", type=str, default="local_scan", help="Prefix for output files (json/csv).")
    p.add_argument("--use-default-common", action="store_true", help="Use default common ports (overrides --ports).")
    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_argparser()
    args = parser.parse_args(argv)

    # choose ports
    if args.use_default_common and args.ports:
        print("Warning: --use-default-common overrides --ports")
    if args.use_default_common or (not args.ports and not args.use_default_common):
        # default behavior: common ports
        ports = sorted(set(DEFAULT_COMMON_PORTS))
    else:
        try:
            ports = parse_ports(args.ports)
        except Exception as e:
            parser.error(f"Invalid --ports: {e}")

    # enforce scanning only localhost
    try:
        # ensure TARGET is resolvable and equals localhost addresses
        ip = socket.gethostbyname(TARGET)
        if ip not in ("127.0.0.1", "::1"):
            print("ERROR: Target must be localhost (127.0.0.1). Exiting.")
            sys.exit(1)
    except Exception:
        print("ERROR: Could not resolve localhost. Exiting.")
        sys.exit(1)

    print(f"Starting local scan of {len(ports)} ports on {TARGET} at {datetime.now().isoformat()}")
    print(f"Concurrency: {args.concurrency}, timeout: {args.timeout}, banner: {args.banner}, send_probe: {args.send_probe}")
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(run_scan(ports, args.concurrency, args.timeout, args.banner, args.send_probe, args.delay_between_starts))
    print_summary(results)
    json_path, csv_path = write_outputs(results, args.out_prefix)
    print(f"\nResults written to: {json_path} and {csv_path}")


if __name__ == "__main__":
    main()
