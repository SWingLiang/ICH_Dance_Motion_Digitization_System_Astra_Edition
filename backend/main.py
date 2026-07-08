from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
CONFIG_PATH = ROOT / "backend" / "config.json"
JOBS_DIR = ROOT / "backend" / "jobs"
DATA_DIR = ROOT / "data" / "sessions"
OUTPUTS_DIR = ROOT / "outputs"
SCRIPTS_DIR = ROOT / "scripts"

for path in [JOBS_DIR, DATA_DIR, OUTPUTS_DIR / "csv", OUTPUTS_DIR / "bvh", OUTPUTS_DIR / "blender", OUTPUTS_DIR / "videos"]:
    path.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ICH Dance Motion Digitization System - Astra Edition",
    version="0.1.0",
    description="Local Web console for Astra RGB-D capture, OpenPose analysis, 3D reconstruction, motion optimization, and Blender export.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class SessionRequest(BaseModel):
    session_id: str = Field(default="demo_session_001")


class CaptureRequest(BaseModel):
    session_id: str = Field(default="demo_session_001")
    duration: int = Field(default=10, ge=1, le=3600)
    fps: int = Field(default=30, ge=1, le=120)


class OpenPoseRequest(BaseModel):
    session_id: str = Field(default="demo_session_001")
    openpose_path: str | None = None
    model: str = "BODY_25"
    use_gpu: bool = True


class OptimizeRequest(BaseModel):
    session_id: str = Field(default="demo_session_001")
    method: str = "moving_average"
    window: int = Field(default=5, ge=1, le=99)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def create_job(task_type: str, session_id: str) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())[:8]
    job = {
        "job_id": job_id,
        "task_type": task_type,
        "session_id": session_id,
        "status": "pending",
        "started_at": None,
        "finished_at": None,
        "log": [],
        "output_files": [],
    }
    write_json(job_path(job_id), job)
    return job


def update_job(job_id: str, **updates: Any) -> Dict[str, Any]:
    path = job_path(job_id)
    job = read_json(path, {})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in updates.items():
        job[key] = value
    write_json(path, job)
    return job


def run_script_job(job: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
    job_id = job["job_id"]
    update_job(job_id, status="running", started_at=now_iso(), log=[f"Running: {' '.join(args)}"])
    try:
        completed = subprocess.run(
            args,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        log = [f"Running: {' '.join(args)}"]
        if completed.stdout:
            log.extend(completed.stdout.strip().splitlines())
        if completed.stderr:
            log.extend(["STDERR:", *completed.stderr.strip().splitlines()])
        status = "finished" if completed.returncode == 0 else "failed"
        output_files = collect_session_files(job["session_id"])
        return update_job(
            job_id,
            status=status,
            finished_at=now_iso(),
            log=log,
            output_files=output_files,
        )
    except Exception as exc:  # pragma: no cover
        return update_job(job_id, status="failed", finished_at=now_iso(), log=[str(exc)])


def collect_session_files(session_id: str) -> List[str]:
    candidates: List[Path] = []
    session_dir = DATA_DIR / session_id
    if session_dir.exists():
        candidates.extend([p for p in session_dir.rglob("*") if p.is_file()])
    for sub in ["csv", "bvh", "blender", "videos"]:
        out_dir = OUTPUTS_DIR / sub
        if out_dir.exists():
            candidates.extend([p for p in out_dir.glob(f"{session_id}*") if p.is_file()])
    return [str(p.relative_to(ROOT)).replace("\\", "/") for p in candidates]


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return "<h1>ICH Dance Motion Digitization System</h1><p>frontend/index.html not found.</p>"
    return index_path.read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "project": "Astra RGB-D + OpenPose Edition", "time": now_iso()}


@app.get("/api/config")
def get_config() -> Dict[str, Any]:
    return read_json(CONFIG_PATH, {})


@app.post("/api/config")
def save_config(config: Dict[str, Any]) -> Dict[str, Any]:
    write_json(CONFIG_PATH, config)
    return {"status": "saved", "config": config}


@app.post("/api/device/test")
def test_device(req: SessionRequest) -> Dict[str, Any]:
    job = create_job("device_test", req.session_id)
    return run_script_job(job, [sys.executable, str(SCRIPTS_DIR / "test_astra_stream.py"), "--session_id", req.session_id])


@app.post("/api/capture/start")
def capture_start(req: CaptureRequest) -> Dict[str, Any]:
    job = create_job("capture_rgbd", req.session_id)
    return run_script_job(
        job,
        [
            sys.executable,
            str(SCRIPTS_DIR / "capture_astra_rgbd.py"),
            "--session_id",
            req.session_id,
            "--duration",
            str(req.duration),
            "--fps",
            str(req.fps),
        ],
    )


@app.post("/api/capture/stop")
def capture_stop(req: SessionRequest) -> Dict[str, Any]:
    return {"status": "stop_requested", "session_id": req.session_id, "note": "Mock capture runs synchronously in V0.1."}


@app.post("/api/openpose/analyze")
def run_openpose(req: OpenPoseRequest) -> Dict[str, Any]:
    job = create_job("openpose_analyze", req.session_id)
    args = [
        sys.executable,
        str(SCRIPTS_DIR / "run_openpose.py"),
        "--session_id",
        req.session_id,
        "--model",
        req.model,
    ]
    if req.openpose_path:
        args.extend(["--openpose_path", req.openpose_path])
    if req.use_gpu:
        args.append("--use_gpu")
    return run_script_job(job, args)


@app.post("/api/reconstruct/3d")
def reconstruct_3d(req: SessionRequest) -> Dict[str, Any]:
    job = create_job("reconstruct_3d", req.session_id)
    return run_script_job(job, [sys.executable, str(SCRIPTS_DIR / "lift_2d_to_3d.py"), "--session_id", req.session_id])


@app.post("/api/motion/optimize")
def optimize_motion(req: OptimizeRequest) -> Dict[str, Any]:
    job = create_job("motion_optimize", req.session_id)
    return run_script_job(
        job,
        [
            sys.executable,
            str(SCRIPTS_DIR / "smooth_motion.py"),
            "--session_id",
            req.session_id,
            "--method",
            req.method,
            "--window",
            str(req.window),
        ],
    )


@app.post("/api/export/csv")
def export_csv(req: SessionRequest) -> Dict[str, Any]:
    job = create_job("export_csv", req.session_id)
    return run_script_job(job, [sys.executable, str(SCRIPTS_DIR / "export_csv.py"), "--session_id", req.session_id])


@app.post("/api/export/bvh")
def export_bvh(req: SessionRequest) -> Dict[str, Any]:
    job = create_job("export_bvh", req.session_id)
    return run_script_job(job, [sys.executable, str(SCRIPTS_DIR / "export_bvh.py"), "--session_id", req.session_id])


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    job = read_json(job_path(job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/sessions")
def list_sessions() -> Dict[str, Any]:
    sessions = sorted([p.name for p in DATA_DIR.iterdir() if p.is_dir()]) if DATA_DIR.exists() else []
    return {"sessions": sessions}


@app.get("/api/files/{session_id}")
def list_files(session_id: str) -> Dict[str, Any]:
    return {"session_id": session_id, "files": collect_session_files(session_id)}


@app.get("/api/download/{file_path:path}")
def download_file(file_path: str) -> FileResponse:
    safe_path = (ROOT / file_path).resolve()
    if not str(safe_path).startswith(str(ROOT.resolve())) or not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(safe_path), filename=safe_path.name)
