import os
import sys
import traceback
from src.topic_manager import TopicManager
from src.researcher import Researcher
from src.script_generator import ScriptGenerator
from src.tts_generator import TTSGenerator
from src.drive_uploader import DriveUploader


def main():
    required_env = ["GOOGLE_API_KEY", "GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET", "GOOGLE_OAUTH_REFRESH_TOKEN"]
    missing = [e for e in required_env if not os.environ.get(e)]
    if missing:
        print(f"環境変数が未設定です: {', '.join(missing)}")
        sys.exit(1)

    topic_manager = TopicManager()
    researcher = Researcher()
    script_gen = ScriptGenerator()
    tts_gen = TTSGenerator()
    drive = DriveUploader()

    topics = topic_manager.select_topics()
    print(f"本日の対象トピック: {len(topics)}件")

    success = 0
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{len(topics)}] {topic['title']}")
        try:
            print("  リサーチ中...")
            research = researcher.research(topic)

            print("  スクリプト生成中...")
            script = script_gen.generate(topic, research)

            print("  音声合成中...")
            audio_path = tts_gen.generate(script, topic)

            print("  Google Driveへアップロード中...")
            drive_url = drive.upload(audio_path, topic)

            topic_manager.mark_as_done(topic, drive_url, audio_path.name)
            audio_path.unlink(missing_ok=True)
            success += 1
            print(f"  完了: {drive_url}")

        except Exception as e:
            print(f"  エラー: {e}")
            traceback.print_exc()

    print(f"\n完了: {success}/{len(topics)} 件のPodcastを作成しました。")


if __name__ == "__main__":
    main()
