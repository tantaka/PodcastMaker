import wave
import os
import re
import yaml
from pathlib import Path
from google import genai
from google.genai import types
from src.utils import gemini_with_retry

# 1セグメントあたりの最大文字数（約2〜3分相当）
SEGMENT_MAX_CHARS = 800


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

    def _split_script(self, script: str) -> list[str]:
        """スクリプトをセリフ単位でSEGMENT_MAX_CHARS以下のセグメントに分割する"""
        lines = [l for l in script.strip().splitlines() if l.strip()]
        segments, current, current_len = [], [], 0
        for line in lines:
            if current_len + len(line) > SEGMENT_MAX_CHARS and current:
                segments.append("\n".join(current))
                current, current_len = [], 0
            current.append(line)
            current_len += len(line)
        if current:
            segments.append("\n".join(current))
        return segments

    def _generate_segment(self, segment: str) -> bytes:
        prompt = f"""以下のPodcast台本を自然な会話として読み上げてください。
{self.male_name}と{self.female_name}の二人が話しています。

{segment}"""

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
        return response.candidates[0].content.parts[0].inline_data.data

    def generate(self, script: str, topic: dict) -> Path:
        segments = self._split_script(script)
        print(f"  スクリプトを {len(segments)} セグメントに分割して音声合成します")

        all_pcm = b""
        for i, segment in enumerate(segments, 1):
            print(f"  セグメント {i}/{len(segments)} 音声合成中...")
            all_pcm += self._generate_segment(segment)

        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic["id"])
        wav_path = self.output_dir / f"{safe_title}.wav"
        self._save_wav(all_pcm, wav_path)
        return wav_path

    def _save_wav(self, pcm_data: bytes, path: Path):
        # Gemini TTS は PCM 24kHz 16bit モノラルで出力
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)
