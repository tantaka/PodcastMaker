import json
import random
from datetime import datetime
from pathlib import Path
import yaml


class TopicManager:
    def __init__(self, topics_path="topics.yaml", history_path="history.json", config_path="config.yaml"):
        self.topics_path = Path(topics_path)
        self.history_path = Path(history_path)

        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.episodes_per_day = config["podcast"]["episodes_per_day"]

    def _load_topics(self):
        with open(self.topics_path, encoding="utf-8") as f:
            return yaml.safe_load(f)["topics"]

    def _load_history(self):
        if not self.history_path.exists():
            return {"completed": []}
        with open(self.history_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_history(self, history):
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def select_topics(self):
        all_topics = self._load_topics()
        history = self._load_history()
        completed_ids = {e["topic_id"] for e in history["completed"]}

        available = [t for t in all_topics if t["id"] not in completed_ids]

        if not available:
            print("全トピック完了。履歴をリセットします。")
            history["completed"] = []
            self._save_history(history)
            available = all_topics

        count = min(self.episodes_per_day, len(available))
        return random.sample(available, count)

    def mark_as_done(self, topic, drive_url, audio_filename):
        history = self._load_history()
        history["completed"].append({
            "topic_id": topic["id"],
            "title": topic["title"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "drive_url": drive_url,
            "filename": audio_filename,
        })
        self._save_history(history)
