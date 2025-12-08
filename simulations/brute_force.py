import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


def _generate_attempts(count: int, target: str) -> List[Dict[str, object]]:
    attempts: List[Dict[str, object]] = []
    start = datetime.now()
    for idx in range(count):
        ts = start + timedelta(milliseconds=120 * idx + random.randint(0, 60))
        dst_port = random.choice([21, 22, 23, 3389])
        syn = random.randint(1, 8)
        ack = random.randint(0, syn // 2)

        attempts.append(
            {
                "timestamp": ts.isoformat() + "Z",
                "src_ip": f"10.0.0.{random.randint(2, 250)}",
                "dst_ip": target,
                "dst_port": dst_port,
                "flow_packets_s": random.uniform(8, 40),
                "flow_duration": random.uniform(180000, 1400000),
                "total_fwd_packet": random.randint(3, 12),
                "syn_flag_count": syn,
                "ack_flag_count": ack,
            }
        )
    return attempts


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate brute force attack feature payloads.")
    parser.add_argument("attempts", type=int, nargs="?", default=25, help="Number of attempts to simulate")
    parser.add_argument("--target", default="192.168.50.253", help="Destination IP for the simulated attack")
    parser.add_argument("--out-file", type=Path, default=None, help="Optional path to write JSON output")
    args = parser.parse_args(argv)

    attempts = _generate_attempts(max(args.attempts, 1), args.target)

    json.dump(attempts, sys.stdout)

    if args.out_file:
        args.out_file.parent.mkdir(parents=True, exist_ok=True)
        with args.out_file.open("w", encoding="utf-8") as f:
            json.dump(attempts, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
