import re
import time
import random
from google.genai import errors as genai_errors
import httpx


def gemini_with_retry(client, model, contents, config, max_retries=8):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except (genai_errors.ServerError, genai_errors.ClientError,
                httpx.RemoteProtocolError, httpx.ReadTimeout) as e:
            if attempt >= max_retries - 1:
                raise

            # 429のretry-after をエラーメッセージから取得
            wait = (2 ** attempt) + random.uniform(0, 1)
            match = re.search(r'retry in (\d+\.?\d*)s', str(e))
            if match:
                wait = float(match.group(1)) + 2

            print(f"  エラー({type(e).__name__})、{wait:.0f}秒後にリトライ ({attempt + 1}/{max_retries})...")
            time.sleep(wait)
