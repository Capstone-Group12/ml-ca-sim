import argparse
import asyncio
import json
import socket
import sys
from datetime import datetime
from typing import List, Tuple

class port_probe:
    TARGET = "192.168.50.253"
    DEFAULT_COMMON_PORTS = list(range(0, 10001))

    def __init__(self, num_ports):
        self.ports = list(range(0, num_ports + 1))
        self.concurrency = 200
        self.timeout = 1.5
        self.banner =True
        self.send_probe = True
        self.delay = 0.0
        self.out_prefix = "local_scan"
        self.use_default_common = False

    @staticmethod
    def parse_ports(ports_spec: str) -> List[int]:
        out = set()
        parts = [p.strip() for p in ports_spec.split(",") if p.strip()]
        for p in parts:
            if "-" in p:
                lo, hi = p.split("-", 1)
                lo, hi = int(lo), int(hi)
                if lo < 1 or hi > 65535 or lo > hi:
                    raise ValueError(f"Invalid range: {p}")
                out.update(range(lo, hi + 1))
            else:
                port = int(p)
                if port < 1 or port > 65535:
                    raise ValueError(f"Invalid port: {p}")
                out.add(port)
        return sorted(out)

    async def try_connect(self, port: int, semaphore: asyncio.Semaphore,
                          start_delay: float) -> Tuple[int, str, str]:
        if start_delay:
            await asyncio.sleep(start_delay)

        async with semaphore:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.TARGET, port),
                    timeout=self.timeout
                )
            except (asyncio.TimeoutError, OSError) as e:
                err = str(e).lower()
                if isinstance(e, asyncio.TimeoutError):
                    return (port, "filtered", "")
                if "refused" in err:
                    return (port, "closed", "")
                return (port, "filtered", "")

            banner_text = ""
            if self.banner:
                try:
                    if self.send_probe:
                        writer.write(b"\r\n")
                        await asyncio.wait_for(writer.drain(), timeout=min(1.0, self.timeout))
                    data = await asyncio.wait_for(reader.read(1024), timeout=min(1.0, self.timeout))
                    if data:
                        try:
                            banner_text = data.decode("utf-8", errors="replace").strip()
                        except Exception:
                            banner_text = repr(data[:200])
                except Exception:
                    pass

            writer.close()
            try: await writer.wait_closed()
            except Exception: pass

            return (port, "open", banner_text)

    async def perform_scan(self):
        semaphore = asyncio.Semaphore(self.concurrency)
        tasks = []
        ports = self.ports

        for i, port in enumerate(ports):
            start_delay = i * self.delay
            task = asyncio.create_task(
                self.try_connect(port, semaphore, start_delay)
            )
            tasks.append(task)

        results = []
        total = len(tasks)
        completed = 0

        for fut in asyncio.as_completed(tasks):
            result = await fut
            results.append(result)
            completed += 1
            print(f"[{completed}/{total}] port {result[0]} -> {result[1]}"
                  f"{(' | banner: ' + result[2][:120]) if result[2] else ''}")

        return sorted(results, key=lambda x: x[0])

    def write_outputs(self, results):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = f"simulations/generated_payloads/{self.out_prefix}_{ts}.json"

        rows = [{
            "timestamp": datetime.now().isoformat(),
            "target": self.TARGET,
            "port": port,
            "state": state,
            "banner": banner
        } for port, state, banner in results]

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(rows, jf, indent=2, ensure_ascii=False)

        return json_path

    @staticmethod
    def print_summary(results):
        open_ports = [p for p, s, _ in results if s == "open"]
        closed_ports = [p for p, s, _ in results if s == "closed"]
        filtered_ports = [p for p, s, _ in results if s == "filtered"]

        print("\nScan summary:")
        print("=============")
        print(f"Total ports scanned: {len(results)}")
        print(f"Open: {len(open_ports)} -> {open_ports[:20]}")
        print(f"Closed: {len(closed_ports)} -> {closed_ports[:20]}")
        print(f"Filtered: {len(filtered_ports)} -> {filtered_ports[:20]}")

        if open_ports:
            print("\nDetected banners:")
            for p, s, b in results:
                if s == "open" and b:
                    print(f" - {p}: {b[:200]}")

    def resolve_ports(self):
        if self.use_default_common or not self.ports:
            self.ports = sorted(set(self.DEFAULT_COMMON_PORTS))
        else:
            self.ports = self.parse_ports(self.ports)

    def run(self):
        self.resolve_ports()

        print(f"Starting local scan of {len(self.ports)} ports on {self.TARGET}")
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.perform_scan())
        self.print_summary(results)
        paths = self.write_outputs(results)
        print(f"\nResults written to: {paths}")


if len(sys.argv) > 1:
    scanner = port_probe(sys.argv[1])
else:
    scanner = port_probe(10000)

scanner.run()
