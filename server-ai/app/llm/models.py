import asyncio
import base64
import httpx
from typing import Any, AsyncIterator, Iterator, List
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_deepseek import ChatDeepSeek

from app.config import settings


def _extract_ocr_sync(image_url: str) -> str:
    if not image_url:
        return ""
    try:
        from rapidocr_onnxruntime import RapidOCR
        img_bytes = None
        if image_url.startswith("data:image"):
            parts = image_url.split(",", 1)
            if len(parts) == 2:
                img_bytes = base64.b64decode(parts[1])
        elif image_url.startswith("http://") or image_url.startswith("https://") or image_url.startswith("/minio/"):
            url = image_url
            if url.startswith("/minio/"):
                endpoint = settings.minio_endpoint if settings.minio_endpoint.startswith("http") else f"http://{settings.minio_endpoint}"
                url = f"{endpoint}{url}"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    img_bytes = resp.content
        if not img_bytes:
            return ""
        ocr = RapidOCR()
        res, _ = ocr(img_bytes)
        if res:
            return "\n".join([str(item[1]) for item in res if item and len(item) > 1])
        return ""
    except Exception as e:
        return f"[视觉提取出错: {str(e)}]"


async def _extract_ocr_async(image_url: str) -> str:
    return await asyncio.to_thread(_extract_ocr_sync, image_url)


def _process_msg_list(messages: List[BaseMessage], ocr_results: List[str]) -> List[BaseMessage]:
    new_messages = []
    ocr_idx = 0
    for msg in messages:
        if isinstance(msg.content, list):
            text_parts = []
            for block in msg.content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "image_url":
                        ocr_txt = ocr_results[ocr_idx] if ocr_idx < len(ocr_results) else ""
                        ocr_idx += 1
                        if ocr_txt:
                            text_parts.append(f"\n[用户上传了图片，视觉OCR识别到的文字内容如下：\n{ocr_txt}\n]")
                        else:
                            text_parts.append("\n[用户上传了图片，未检测到明显文字或为非文字图片]")
            new_msg = msg.model_copy(update={"content": "".join(text_parts)})
            new_messages.append(new_msg)
        else:
            new_messages.append(msg)
    return new_messages


class MultimodalChatDeepSeek(ChatDeepSeek):
    def _sanitize_messages_sync(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        image_urls = []
        for msg in messages:
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "image_url":
                        img_info = block.get("image_url", {})
                        url = img_info.get("url", "") if isinstance(img_info, dict) else str(img_info)
                        image_urls.append(url)
        if not image_urls:
            return messages
        ocr_results = [_extract_ocr_sync(url) for url in image_urls]
        return _process_msg_list(messages, ocr_results)

    async def _sanitize_messages_async(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        image_urls = []
        for msg in messages:
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "image_url":
                        img_info = block.get("image_url", {})
                        url = img_info.get("url", "") if isinstance(img_info, dict) else str(img_info)
                        image_urls.append(url)
        if not image_urls:
            return messages
        ocr_results = await asyncio.gather(*[_extract_ocr_async(url) for url in image_urls])
        return _process_msg_list(messages, ocr_results)

    def _stream(self, messages: List[BaseMessage], stop: Any = None, **kwargs: Any) -> Iterator[ChatGenerationChunk]:
        clean_messages = self._sanitize_messages_sync(messages)
        return super()._stream(clean_messages, stop=stop, **kwargs)

    async def _astream(self, messages: List[BaseMessage], stop: Any = None, **kwargs: Any) -> AsyncIterator[ChatGenerationChunk]:
        clean_messages = await self._sanitize_messages_async(messages)
        async for chunk in super()._astream(clean_messages, stop=stop, **kwargs):
            yield chunk

    def _generate(self, messages: List[BaseMessage], stop: Any = None, **kwargs: Any) -> ChatResult:
        clean_messages = self._sanitize_messages_sync(messages)
        return super()._generate(clean_messages, stop=stop, **kwargs)

    async def _agenerate(self, messages: List[BaseMessage], stop: Any = None, **kwargs: Any) -> ChatResult:
        clean_messages = await self._sanitize_messages_async(messages)
        return await super()._agenerate(clean_messages, stop=stop, **kwargs)


def create_deepseek() -> MultimodalChatDeepSeek:
    return MultimodalChatDeepSeek(
        api_key=settings.deepseek_api_key,
        model=settings.deepseek_api_model,
        temperature=1.3,
        max_tokens=4396,
        streaming=True,
    )


def create_deepseek_reasoner() -> MultimodalChatDeepSeek:
    return MultimodalChatDeepSeek(
        api_key=settings.deepseek_api_key,
        model=settings.deepseek_reasoner_api_model,
        temperature=1.3,
        max_tokens=18000,
        streaming=True,
    )
