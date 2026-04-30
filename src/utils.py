import time
import random
from google.genai.errors import ServerError


def gemini_with_retry(client, model, contents, config, max_retries=6):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except ServerError as e:
            if attempt < max_retries - 1:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  503エラー、{wait:.0f}秒後にリトライ ({attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
