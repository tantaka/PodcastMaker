import feedparser
import requests
import yaml
from google import genai
from google.genai import types


WIKIPEDIA_API = "https://ja.wikipedia.org/w/api.php"
NEWS_RSS_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"


class Researcher:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.model = config["gemini"]["research_model"]
        self.client = genai.Client()

    def _fetch_news(self, keywords: list[str]) -> list[dict]:
        query = " OR ".join(keywords[:3])
        url = NEWS_RSS_TEMPLATE.format(query=requests.utils.quote(query))
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
            })
        return articles

    def _fetch_wikipedia(self, keyword: str) -> str:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": keyword,
            "redirects": 1,
        }
        try:
            resp = requests.get(WIKIPEDIA_API, params=params, timeout=10)
            pages = resp.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()))
            return page.get("extract", "")[:2000]
        except Exception:
            return ""

    def research(self, topic: dict) -> str:
        news_articles = self._fetch_news(topic["keywords"])
        wiki_text = self._fetch_wikipedia(topic["keywords"][0])

        news_text = "\n".join(
            f"- {a['title']} ({a['published']})\n  {a['summary']}"
            for a in news_articles
        )

        prompt = f"""以下のトピックについて、Podcastの台本作成に必要な深いリサーチをまとめてください。

トピック: {topic['title']}
カテゴリ: {topic['category']}

【最新ニュース】
{news_text}

【Wikipedia情報】
{wiki_text}

以下の観点で詳細にまとめてください（日本語で2000文字程度）：
1. このトピックの概要・背景
2. 現在の状況・最新動向
3. 主要な課題・論点
4. 専門家や業界の見解
5. 今後の展望・影響

情報は正確に、深く、多角的にまとめてください。"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=3000,
            ),
        )
        return response.text
