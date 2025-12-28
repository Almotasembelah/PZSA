# 🍕 Pizza Store Assistant: Hygiene Compliance System

This project is a **Computer Vision (CV) monitoring system** designed to ensure hygiene protocol compliance in pizza preparation areas. The system specifically monitors whether staff members use a **scooper** when handling specific ingredients (e.g., proteins) within designated Regions of Interest (ROIs).

Any instance of a worker picking up ingredients without a scooper is automatically flagged as a hygiene violation.

---

## 📂 Project Structure

```

PZSA
├── PZSA/                        # Main source code package
│   ├── configs/                 # System configuration (DB, Kafka, Logging)
│   ├── data/                    # Database layer: CRUD operations and ORM entities
│   |── controller/              # Logic for managing violation events (adding to db)
│   ├── services/                
│   │   ├── detection/           # Core CV logic (YOLO inference & violation rules)
│   │   ├── frame_reader/        # Handles video ingestion and frame extraction
│   │   └── streaming/           # Manages Kafka data streams
│   └── ui/                      # Web interface (Flask app and HTML templates)
├── scripts/                     # Bash utilities for setup, Kafka, and deployment
├── resources/                   # Static assets and project resources
|   ├── violations/              # Storage for recorded violation images
|   └── model/                   # Pre-trained YOLO weights (.pt files)
│       └── yolo12m-v2.pt        # Main model (Hands, Pizza, Scooper)
├── logs/                        # System and error log files
├── docker-compose.yml           # Container orchestration for App and Kafka
├── Dockerfile                   # Build instructions for the App container
├── pyproject.toml               # Python dependencies and project metadata
├── uv.lock 
├── btrack.yaml                  # Configuration for BOTSort tracking
└── README.md                    # Project documentation

```
---
## 🏗️ System Design

The system utilizes a distributed architecture to handle video processing and event logging.

* **Core Logic:** Processes video frames, detects objects, and evaluates ROI-based rules.
* **Messaging:** Uses **Kafka** to handle real-time violation alerts and data streams.
* **Documentation:** Detailed architectural diagrams and design decisions can be found in the [Project Wiki](https://github.com/Almotasembelah/PZSA/wiki).

---

## Output

<video width="640" height="480" controls>
  <source src="resources/output/output.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

---
## 🚀 Setup & Installation

### Prerequisites

* **Python:** v3.12 or higher
* **Kafka:** Service must be reachable

### Local Environment Setup

1. **Initialize Environment:**
```bash
source ./scripts/setup.sh
```


2. **Configure Kafka:**
If you are running Kafka via Docker, export your Container ID:
```bash
export CONTAINER_ID='your_kafka_container_id'
```


3. **Initialize Topics:**
This script will remove existing topics and recreate them to ensure a clean state.
```bash
source ./scripts/topics.sh
```


4. **Launch Services:**
```bash
source ./scripts/run.sh
```


5. **Access Dashboard:** Open [http://127.0.0.1:5000](https://www.google.com/search?q=http://127.0.0.1:5000) in your browser.

### Docker Installation

If you prefer a containerized setup, use the provided Compose file:

```bash
docker compose up --build
```

Access the system at [http://127.0.0.1:5000](https://www.google.com/search?q=http://127.0.0.1:5000).

---

## 🧠 Model Details

### Detection Strategy

The system uses a two-model approach to overcome tracking instabilities:

| Model | Task | Purpose |
| --- | --- | --- |
| **YOLO12m** | Main Detection | Detects Hands, Persons, Pizza, and Scoopers. |
| **YOLO11s** | Tracking Anchor | Detects Persons to provide a stable ID reference for hands. |

### Technical Challenges & Solutions

* **Hand Tracking Stability:** Because the current YOLO12m model occasionally loses Hand detections across frames (causing "ID jumping"), we assign detected Hands to the nearest **Person ID**. This ensures that even if a hand detection flickers, the action is attributed to a consistent individual.
* **Inference Overhead:** The dual-model approach increases tracking stability but adds computational cost, resulting in slower frame processing.
* **Dataset Limitations:** The current training set for scoopers is small. This can result in:
* Occasional failure to detect the scooper.
* **False Positives:** The system may flag a violation even if a scooper is used, simply because the model failed to see the tool.

---

## 🛠️ TODO

To move this project toward a production-ready state, the following optimizations are planned:

* **Inference Speed:** Implement batch processing instead of single-frame processing.
* **Optimization:** Convert models to **TensorRT** or **ONNX** for high-performance deployment.
* **Model Robustness:** Expand the training dataset to improve scooper detection and reduce false violation flags.