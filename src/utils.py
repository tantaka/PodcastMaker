import time
import random
from google.genai.errors import ServerError
import httpx


def gemini_with_retry(client, model, contents, config, max_retries=6):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except (ServerError, httpx.RemoteProtocolError, httpx.ReadTimeout) as e:
            if attempt < max_retries - 1:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  エラー({type(e).__name__})、{wait:.0f}秒後にリトライ ({attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
