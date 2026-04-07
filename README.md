# Smart Parking Security Dashboard

Live dashboard for a multi-layer smart parking security system built on NVIDIA Jetson Nano.

**Live Demo:** [View Dashboard](https://wannazirulhafiz.github.io/parking-dashboard/)

## System Architecture

```
RTSP Camera → Jetson Nano (Edge AI)
                  ├── Layer 1: Canny Edge Detection (Parking Occupancy)
                  ├── Layer 2: Privacy-by-Design (No raw data to cloud)
                  └── Layer 3: SHA-256 Hash Chain → AWS DynamoDB (Cloud Anchor)
```

## Dashboard Features

- Real-time parking slot occupancy (15 slots)
- Blockchain integrity status (SHA-256 hash chain)
- System performance metrics (CPU, RAM, GPU via tegrastats)
- Cloud sync status (AWS DynamoDB)

## Tech Stack

- **Edge Device:** NVIDIA Jetson Nano (ARM64)
- **Detection:** OpenCV Canny edge detection + polygon ROIs
- **Integrity:** Lightweight blockchain (SHA-256 hash chain + SQLite)
- **Cloud:** AWS S3 (frames) + DynamoDB (checkpoints)
- **Dashboard:** Vanilla HTML/CSS/JS + Chart.js, hosted on GitHub Pages

## Master Thesis

This project is part of a Master's thesis on multi-layer security frameworks for edge-based smart parking systems.

**Author:** Nazirul Hafiz
**Device:** NVIDIA Jetson Nano
**Experiments:** 14 experiments (E1–E10 tamper detection + P1–P4 performance benchmarks)
