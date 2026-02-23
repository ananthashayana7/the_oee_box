# Setup Guide - The OEE Box

The easiest way to build and run the application is using **Docker Compose**. This ensures all dependencies (MQTT Broker, FastAPI Backend, React Frontend, and Simulator) are configured correctly.

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

## Quick Start (Docker)

1.  **Open a terminal** in the project root (`C:\OEE_Box\the_oee_box`).
2.  **Build and Start** the entire stack:
    ```bash
    docker-compose up --build -d
    ```
    *This will download images, build the backend/frontend containers, and start them in the background.*

3.  **Access the Application**:
    - **Frontend (Dashboard)**: [http://localhost](http://localhost) (or port 80)
    - **Backend (API)**: [http://localhost:8000](http://localhost:8000)
    - **MQTT Broker**: Exposed on `localhost:1883`

## Manual Mode (Development)

If you prefer to run components manually:

### 1. Backend
```bash
# Install dependencies
pip install -r requirements.txt
# Start the API
uvicorn backend.main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
# Dashboard available at http://localhost:5173
```

### 3. Simulator
```bash
python simulator.py
```

## Stopping the App
To shut down the Docker containers:
```bash
docker-compose down
```
