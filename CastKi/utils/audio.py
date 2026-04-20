from __future__ import annotations

try:
    import sounddevice as sd
    import numpy as np
    _SD_AVAILABLE = True
except ImportError:
    _SD_AVAILABLE = False


def _find_device(name_fragment: str, require_input: bool) -> tuple[int, int] | None:
    """Return (device_index, channel_count) or None."""
    key = "max_input_channels" if require_input else "max_output_channels"
    for i, d in enumerate(sd.query_devices()):
        if name_fragment.lower() in d["name"].lower() and d[key] > 0:
            return i, d[key]
    return None


class AudioPassthrough:
    def __init__(self) -> None:
        self._stream = None
        self._volume: float = 0.8

        if not _SD_AVAILABLE:
            return

        result = _find_device("shadowcast", require_input=True)
        if result is None:
            print("[audio] ShadowCast audio input not found")
            return

        in_idx, in_ch = result
        devices = sd.query_devices()
        samplerate = int(devices[in_idx]["default_samplerate"])
        channels = min(in_ch, 2)

        # Use the OS default output (sd.default.device[1] is the true system default)
        out_idx = sd.default.device[1]
        print(f"[audio] {devices[in_idx]['name']} -> {devices[out_idx]['name']} @ {samplerate}Hz")

        def _callback(indata, outdata, frames, time, status):
            if status:
                print(f"[audio] {status}")
            np.multiply(indata[:, :channels], self._volume, out=outdata[:, :channels])

        try:
            self._stream = sd.Stream(
                device=(in_idx, out_idx),
                samplerate=samplerate,
                channels=channels,
                dtype="float32",
                blocksize=256,
                callback=_callback,
            )
            self._stream.start()
            print("[audio] passthrough started")
        except Exception as e:
            print(f"[audio] failed to start stream: {e}")
            self._stream = None

    @property
    def available(self) -> bool:
        return self._stream is not None

    def set_volume(self, level: float) -> None:
        self._volume = max(0.0, min(1.0, level))

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
