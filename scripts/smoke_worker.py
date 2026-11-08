import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

root = Path(__file__).resolve().parents[1]
model_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    __import__("os").environ.get("LOCALAPPDATA", "")
) / "ARIS" / "models" / "vosk-model-small-en-in-0.4"
worker_path = root / "voice" / "worker.py"
lines = queue.Queue()


def collect_output(process):
    for line in process.stdout:
        lines.put(line)


process = subprocess.Popen(
    [sys.executable, str(worker_path), str(model_path)],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    bufsize=1,
)
threading.Thread(target=collect_output, args=(process,), daemon=True).start()

try:
    first = json.loads(lines.get(timeout=60))
    if first.get("type") != "ready":
        raise SystemExit("Voice worker did not report ready: " + str(first))
    process.stdin.write(json.dumps({"action": "shutdown"}) + "\n")
    process.stdin.flush()
    exit_code = process.wait(timeout=20)
    if exit_code != 0:
        raise SystemExit("Voice worker exited with code " + str(exit_code))
    print("Voice worker loaded the offline model and shut down cleanly (no microphone opened).")
finally:
    if process.poll() is None:
        process.kill()
