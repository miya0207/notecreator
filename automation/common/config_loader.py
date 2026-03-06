"""設定読み込みモジュール: .env + YAML設定を統合"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
OUT_DIR = BASE_DIR / "out"


@dataclass
class Config:
    anthropic_api_key: str
    topics: dict
    affiliate: dict
    base_dir: Path = field(default=BASE_DIR)
    out_dir: Path = field(default=OUT_DIR)


def load_config() -> Config:
    """設定をすべて読み込んで Config を返す"""
    load_dotenv(BASE_DIR / ".env", override=True)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("警告: ANTHROPIC_API_KEY が設定されていません (.env を確認してください)")

    with open(CONFIG_DIR / "topics.yml", encoding="utf-8") as f:
        topics = yaml.safe_load(f)

    with open(CONFIG_DIR / "affiliate.yml", encoding="utf-8") as f:
        affiliate = yaml.safe_load(f)

    return Config(
        anthropic_api_key=api_key,
        topics=topics,
        affiliate=affiliate,
    )


if __name__ == "__main__":
    cfg = load_config()
    print(f"API Key: {'設定済み' if cfg.anthropic_api_key else '未設定'}")
    print(f"ジャンル数: {len(cfg.topics.get('genres', []))}")
    print(f"広告カテゴリ数: {len(cfg.affiliate.get('categories', []))}")
