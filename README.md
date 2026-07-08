# ICH Dance Motion Digitization System — Astra RGB-D + OpenPose Edition

A low-cost RGB-D motion digitization workstation for intangible cultural heritage (ICH) dance and performance analysis.

This project upgrades the previous low-cost dual-camera motion capture idea into a practical single RGB-D depth camera pipeline based on **Orbbec Astra Pro S M + OpenPose BODY_25 + 2D-to-3D depth lifting + motion optimization + CSV/BVH/Blender export**.

## Core idea

The system does **not** ask the HTML page to run Python directly. Instead, it uses a local web control panel:

```text
HTML / CSS / JavaScript UI
        ↓ REST API
FastAPI local backend
        ↓ subprocess / Python modules
Astra capture / OpenPose analysis / 3D reconstruction / motion export
```

This design avoids the old difficulty of dual-camera calibration. The Astra depth camera provides RGB + depth frames, OpenPose detects 2D body keypoints, and the system samples depth at each keypoint to reconstruct 3D coordinates.

## Pipeline

```text
Astra RGB-D Camera
        ↓
RGB + Depth Capture
        ↓
OpenPose BODY_25 2D Keypoint Detection
        ↓
Depth Sampling at Keypoints
        ↓
2D + Depth → 3D Coordinates (x, y, z)
        ↓
Temporal Smoothing / Missing Joint Repair
        ↓
ICH Skeleton Mapping
        ↓
CSV / JSON / BVH / Blender Export
```

## Project structure

```text
ICH_Dance_Motion_Digitization_System_Astra_Edition/
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── config.json
│   └── jobs/
├── scripts/
│   ├── test_astra_stream.py
│   ├── capture_astra_rgbd.py
│   ├── run_openpose.py
│   ├── lift_2d_to_3d.py
│   ├── smooth_motion.py
│   ├── export_csv.py
│   ├── export_bvh.py
│   └── blender_import_motion.py
├── data/
│   └── sessions/
├── outputs/
│   ├── csv/
│   ├── bvh/
│   ├── blender/
│   └── videos/
└── README.md
```

## Current version

This first version is a **mock runnable prototype**. It creates the complete interface and API structure, but uses generated sample data instead of real Astra/OpenPose data.

The purpose of this version is to make the full workflow executable first:

1. Device test
2. RGB-D motion capture session
3. OpenPose mock JSON generation
4. 2D + depth to 3D CSV reconstruction
5. Motion smoothing
6. CSV/BVH/Blender export

After this structure runs successfully, the mock scripts can be replaced by real Astra OpenNI/Orbbec SDK and OpenPoseDemo.exe calls.

## Local run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

```text
http://localhost:8000
```

## API endpoints

```text
GET  /api/health
GET  /api/config
POST /api/config
POST /api/device/test
POST /api/capture/start
POST /api/capture/stop
POST /api/openpose/analyze
POST /api/reconstruct/3d
POST /api/motion/optimize
POST /api/export/csv
POST /api/export/bvh
GET  /api/jobs/{job_id}
GET  /api/sessions
GET  /api/files/{session_id}
```

## Future hardware integration

Replace mock logic in:

```text
scripts/test_astra_stream.py
scripts/capture_astra_rgbd.py
```

with real Astra/OpenNI/Orbbec SDK calls.

Recommended first hardware checks:

```text
RGB frame preview
Depth frame preview
Frame timestamp
Camera intrinsics
Depth scale
Depth-to-RGB alignment
```

## Future OpenPose integration

Replace mock logic in:

```text
scripts/run_openpose.py
```

with a real OpenPoseDemo command, for example:

```bash
OpenPoseDemo.exe \
  --video data/sessions/<session_id>/rgb.mp4 \
  --write_json data/sessions/<session_id>/openpose_json \
  --display 0 \
  --render_pose 1 \
  --model_pose BODY_25
```

## Research positioning

This system is designed for low-cost, explainable, reproducible ICH dance digitization. It can support:

- traditional dance motion capture
- Yingge dance step analysis
- lion dance body mapping
- Nuo dance gesture reconstruction
- OpenPose-to-cultural-skeleton remapping
- Blender-based digital twin visualization
- CSV-based motion dataset construction
