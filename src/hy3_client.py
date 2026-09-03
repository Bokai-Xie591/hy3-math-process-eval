"""Hy3 API 封装：OpenAI 兼容接口 + 简单重试 + JSON 提取工具。"""
import json
import re
import time

from openai import OpenAI

from .config import Settings, load_settings


class Hy3Client:
    def __init__(self, settings: Settings | None = None, max_retries: int = 3):
        self.settings = settings or load_settings()
        self.client = OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url)
        self.max_retries = max_retries

    def chat(self, messages: list[dict], temperature: float = 0.2,
             want_json: bool = False, max_tokens: int = 4096) -> str:
        kwargs = {}
        if want_json:
            kwargs["response_format"] = {"type": "json_object"}
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self.client.chat.completions.create(
                    model=self.settings.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # noqa: BLE001
                last_err = e
                # 某些接口不支持 response_format，降级为纯文本 + 后处理提取
                if want_json and "response_format" in str(e):
                    want_json = False
                    kwargs.pop("response_format", None)
                    continue
                time.sleep(2 * (attempt + 1))
        raise last_err  # type: ignore[misc]


def extract_json(text: str) -> dict:
    """从模型输出中提取第一个 JSON 对象（容忍前后多余文字）。"""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"输出中未找到 JSON 对象：{text[:200]}")
    return json.loads(m.group(0))
