from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "sessions"


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock Astra RGB-D device test.")
    parser.add_argument("--session_id", default="demo_session_001")
    args = parser.parse_args()

    session_dir = DATA_DIR / args.session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "device": "Orbbec Astra Pro S M",
        "mode": "mock",
        "rgb_stream": "ok",
        "depth_stream": "ok",
        "fps": 30,
        "resolution": "640x480",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "next_step": "Replace mock logic with OpenNI2 / Orbbec SDK device query.",
    }
    out_path = session_dir / "device_test_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Astra mock device test passed: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
