import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


def generate_attempts(count: int, target: str) -> List[Dict[str, object]]:
    attempts: List[Dict[str, object]] = []
    start = datetime.utcnow()
    for i in range(count):
        # simulate slightly jittered timestamps for sequential attempts
        ts = start + timedelta(milliseconds=150 * i + random.randint(0, 75))
        dst_port = random.choice([21, 22, 23, 3389])

        attempts.append(
            {
                "timestamp": ts.isoformat() + "Z",
                "src_ip": f"10.0.0.{random.randint(1, 254)}",
                "dst_ip": target,
                "dst_port": dst_port,
                "flow_packets_s": random.uniform(5, 45),
                "flow_duration": random.uniform(250000, 1800000),
                "total_fwd_packet": random.randint(3, 15),
                "syn_flag_count": random.randint(1, 8),
                "ack_flag_count": random.randint(0, 4),
            }
        )

    return attempts


def write_output(attempts: List[Dict[str, object]], out_file: Path) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(attempts, f, indent=2)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate brute force attack attempts as JSON.")
    parser.add_argument("attempts", type=int, nargs="?", default=25, help="Number of attempts to simulate")
    parser.add_argument("--target", default="192.168.50.253", help="Destination IP for the simulated attack")
    parser.add_argument(
        "--out-file",
        type=Path,
        default=None,
        help="Optional path to also write the generated JSON payloads",
    )

    args = parser.parse_args(argv)

    attempts = generate_attempts(max(args.attempts, 1), args.target)

    # emit JSON to stdout for callers (API service) to consume
    json.dump(attempts, sys.stdout)

    if args.out_file:
        write_output(attempts, args.out_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
