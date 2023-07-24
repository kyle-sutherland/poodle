import queue
import sys
import sounddevice as sd

from vosk import Model, KaldiRecognizer

q = queue.Queue()


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


def main():
    model = Model(lang='en-us')
    device_info = sd.query_devices(None, "input")
    samplerate = int(device_info["default_samplerate"])
    dump_fn = open("audio_dumps/dump.wav", "wb")

    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=None, dtype="int16", channels=1,
                           callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                print(rec.Result())
            else:
                print(rec.PartialResult())
            if dump_fn is not None:
                dump_fn.write(data)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Quit")
        sys.exit(0)
    except Exception as e:
        sys.exit(type(e).__name__ + ": " + str(e))
