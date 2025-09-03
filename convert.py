import speech_recognition as sr
import subprocess
import os

class Converter:
    def __init__(self, path_to_file: str, language: str = "ru-RU"):
        self.language = language

        base, _ = os.path.splitext(path_to_file)
        wav_path = base + ".wav"

        subprocess.run([
            r'C:\Users\Himitsu\Desktop\Projects\MyBot\ffmpeg\bin\ffmpeg.exe',
            '-v', 'quiet',
            '-i', path_to_file,
            wav_path
        ])

        self.wav_file = wav_path

    def audio_to_text(self) -> str:
        r = sr.Recognizer()
        full_text = []

        with sr.AudioFile(self.wav_file) as source:
            while True:
                try:
                    audio = r.record(source, duration=60)
                    if not audio.get_raw_data():
                        break
                    text = r.recognize_google(audio, language=self.language)
                    full_text.append(text)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    break

        if os.path.exists(self.wav_file):
            os.remove(self.wav_file)

        return " ".join(full_text)