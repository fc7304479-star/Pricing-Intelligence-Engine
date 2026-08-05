import subprocess
import time
import webbrowser

print("=" * 70)
print("Pricing Intelligence Engine")
print("=" * 70)

# -----------------------------
# Start Worker
# -----------------------------
worker = subprocess.Popen(
    ["python", "run_worker.py"]
)

print("[✓] Redis Worker Started")

time.sleep(2)

# -----------------------------
# Start FastAPI
# -----------------------------
api = subprocess.Popen(
    [
        "uvicorn",
        "pricing_engine.api.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
)

print("[✓] FastAPI Started")

time.sleep(3)

webbrowser.open("http://127.0.0.1:8000/docs")

# -----------------------------
# Run Spider
# -----------------------------
print("[✓] Starting Spider...")

subprocess.run(
    [
        "scrapy",
        "crawl",
        "demo_shop",
    ]
)

print("=" * 70)
print("Pipeline Finished Successfully")
print("=" * 70)

worker.terminate()
api.terminate()