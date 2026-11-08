import importlib.util
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aris_voice_worker", root / "voice" / "worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
devices = worker.enumerate_devices()
if devices["defaultInputId"]:
    default_index = worker.resolve_device_id(devices["defaultInputId"], "inputs")
    if default_index is None:
        raise SystemExit("Default input did not resolve.")
if devices["defaultOutputId"]:
    if worker.resolve_device_id(devices["defaultOutputId"], "outputs") is None:
        raise SystemExit("Default output did not resolve.")
settings_path = Path(os.environ.get("APPDATA", "")) / "aris-desktop" / "settings.json"
try:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    settings = {}
saved_input = settings.get("audioInputDeviceId", "")
selected_input = next((device for device in devices["inputs"] if device["id"] == saved_input), None)
if selected_input:
    selected_index = worker.resolve_device_id(saved_input, "inputs")
    supported_rate = worker.choose_input_sample_rate(selected_index)
    print("Saved microphone format check passed: {} via {} at {} Hz; no input stream opened.".format(selected_input["name"], selected_input["hostApi"], supported_rate))
else:
    print("No saved microphone route is currently available; format probing skipped.")
print("Audio device enumeration passed: {} inputs, {} outputs; no streams opened.".format(len(devices["inputs"]), len(devices["outputs"])))
