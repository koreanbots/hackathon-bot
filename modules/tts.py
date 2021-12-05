import asyncio

from io import BytesIO

from gtts import gTTS


def _generate_tts(text: str) -> BytesIO:
    file = BytesIO()
    tts = gTTS(text=text, lang="ko")
    tts.write_to_fp(file)
    file.seek(0)
    return file


async def generate_tts(text: str, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()) -> BytesIO:
    return await loop.run_in_executor(None, _generate_tts, text)
