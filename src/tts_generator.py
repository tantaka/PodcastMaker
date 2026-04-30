import wave
import os
import yaml
from pathlib import Path
from google import genai
from google.genai import types
from src.utils import gemini_with_retry


class TTSGenerator:
    def __init__(self, config_path="config.yaml", output_dir="output"):
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.model = config["gemini"]["tts_model"]
        self.male_name = config["speakers"]["male"]["name"]
        self.male_voice = config["speakers"]["male"]["voice"]
        self.female_name = config["speakers"]["female"]["name"]
        self.female_voice = config["speakers"]["female"]["voice"]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.client = genai.Client()

    def generate(self, script: str, topic: dict) -> Path:
        prompt = f"""以下のPodcast台本を、自然な会話として読み上げてください。
{self.male_name}と{self.female_name}の二人が話しています。

{script}"""

        response = gemini_with_retry(
            self.client, self.model, prompt,
            types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker=self.male_name,
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=self.male_voice,
                                    )
                                ),
                            ),
                            types.SpeakerVoiceConfig(
                                speaker=self.female_name,
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=self.female_voice,
                                    )
                                ),
                            ),
                        ]
                    )
                ),
            ),
        )

        audio_data = response.candidates[0].content.parts[0].inline_data.data
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic["id"])
        wav_path = self.output_dir / f"{safe_title}.wav"
        self._save_wav(audio_data, wav_path)
        return wav_path

    def _save_wav(self, pcm_data: bytes, path: Path):
        # Gemini TTSはPCM 24kHz 16bit モノラルで出力
        sample_rate = 24000
        channels = 1
        sample_width = 2  # 16bit

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
