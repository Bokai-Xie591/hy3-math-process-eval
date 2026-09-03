"""读取环境变量配置。API Key 只允许来自 .env 或系统环境变量。"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str


def load_settings() -> Settings:
    key = os.getenv("HY3_API_KEY", "").strip()
    if not key or key == "在这里填入你的Key":
        raise RuntimeError(
            "缺少 HY3_API_KEY：请复制 .env.example 为 .env 并填入你的 Key，"
            "或用系统环境变量传入（不要把 Key 写进代码或提交进仓库）"
        )
    return Settings(
        api_key=key,
        base_url=os.getenv("HY3_BASE_URL", "https://api.hunyuan.cloud.tencent.com/v1"),
        model=os.getenv("HY3_MODEL", "hy3"),
    )
