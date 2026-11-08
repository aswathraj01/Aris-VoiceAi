import importlib.util
from pathlib import Path
import os

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aris_voice_worker", root / "voice" / "worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
devices = worker.enumerate_devices()
if devices["defaultInputId"]:
    if worker.resolve_device_id(devices["defaultInputId"], "inputs") is None:
        raise SystemExit("Default input did not resolve.")
if devices["defaultOutputId"]:
    if worker.resolve_device_id(devices["defaultOutputId"], "outputs") is None:
        raise SystemExit("Default output did not resolve.")
print("Audio device enumeration passed: {} inputs, {} outputs; no streams opened.".format(len(devices["inputs"]), len(devices["outputs"])))
