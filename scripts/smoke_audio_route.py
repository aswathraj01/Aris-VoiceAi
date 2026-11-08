import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aris_voice_worker", root / "voice" / "worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
worker.selected_output_device_id = "test-output-route"
captured = {}
playback_count = 0

def fake_resolve(device_id, direction):
    if device_id != "test-output-route" or direction != "outputs":
        raise AssertionError("Unexpected output route lookup.")
    return 7

def fake_play(data, samplerate, device, blocking):
    global playback_count
    playback_count += 1
    captured.update({"frames": len(data), "samplerate": samplerate, "device": device, "blocking": blocking})

worker.resolve_device_id = fake_resolve
worker.sd.play = fake_play
worker.speak_text(worker.WAKE_ACKNOWLEDGMENT)
worker.speak_text("ARIS response speech test.")
if playback_count != 2 or captured.get("device") != 7 or not captured.get("frames") or not captured.get("samplerate") or captured.get("blocking") is not True:
    raise SystemExit("Selected output route was not passed to audio playback.")
print("Selected output routing and the “Mm-hmm” wake acknowledgment synthesized successfully; playback was mocked, no sound emitted.")
