import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aris_voice_worker", root / "voice" / "worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
worker.speech_engine = worker.pyttsx3.init()
worker.selected_output_device_id = "test-output-route"
captured = {}

def fake_resolve(device_id, direction):
    if device_id != "test-output-route" or direction != "outputs":
        raise AssertionError("Unexpected output route lookup.")
    return 7

def fake_play(data, samplerate, device, blocking):
    captured.update({"frames": len(data), "samplerate": samplerate, "device": device, "blocking": blocking})

worker.resolve_device_id = fake_resolve
worker.sd.play = fake_play
worker.speak_text("ARIS audio route test.")
worker.speech_engine.stop()
if captured.get("device") != 7 or not captured.get("frames") or not captured.get("samplerate") or captured.get("blocking") is not True:
    raise SystemExit("Selected output route was not passed to audio playback.")
print("Selected output routing passed with synthesized audio; playback was mocked, no sound emitted.")
