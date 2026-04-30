import yaml
from google import genai
from google.genai import types
from src.utils import gemini_with_retry


class ScriptGenerator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.model = config["gemini"]["research_model"]
        self.male_name = config["speakers"]["male"]["name"]
        self.female_name = config["speakers"]["female"]["name"]
        self.min_min = config["podcast"]["min_duration_minutes"]
        self.max_min = config["podcast"]["max_duration_minutes"]
        self.client = genai.Client()

    def generate(self, topic: dict, research: str) -> str:
        # 日本語の話速: 約350文字/分。15-20分 = 5,250〜7,000文字
        min_chars = self.min_min * 350
        max_chars = self.max_min * 350

        prompt = f"""あなたはプロのPodcast台本ライターです。
以下のリサーチ情報をもとに、{self.min_min}〜{self.max_min}分（{min_chars}〜{max_chars}文字）の
深いPodcast台本を日本語で作成してください。

【トピック】{topic['title']}
【カテゴリ】{topic['category']}

【リサーチ情報】
{research}

【台本のルール】
- 話者は2名：{self.male_name}（男性、論理的・分析的な視点）と{self.female_name}（女性、共感的・実践的な視点）
- 形式: "{self.male_name}: セリフ" または "{self.female_name}: セリフ" で記述
- 単なるニュース紹介ではなく、背景・原因・影響・今後の展望を深く掘り下げること
- 専門用語は分かりやすく解説する
- 二人が議論・深掘りし合う対話形式にする
- リスナーが考えるための問いかけを含める

【台本構成】
1. 掴みのイントロ（1〜2分）：リスナーの興味を引く導入
2. 背景・歴史的文脈（3〜4分）：なぜ今このトピックが重要か
3. 核心的な分析・詳細解説（6〜8分）：深い掘り下げ、多角的な視点
4. 影響・今後の展望（3〜4分）：社会・産業・個人への影響
5. まとめとリスナーへの問いかけ（1〜2分）：考えるヒントを残す

必ず{min_chars}文字以上の台本を作成してください。台本のみを出力し、説明文は不要です。"""

        response = gemini_with_retry(
            self.client, self.model, prompt,
            types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192),
        )
        return response.text
