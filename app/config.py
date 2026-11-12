"""应用路径、默认配置与数值归一化。"""

from __future__ import annotations

import copy
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
WEB_PROFILE_DIR = BASE_DIR / "web_profile"

APP_NAME = "7881 自动报价"

DEFAULT_SCRIPTS = [
    "出的价直接签同意就报价就可以了，手续费都是我这边的，给您的就是您到手的一个价",
    "或者对价格不满意你和我说下，我这边可以申请的，这边尽量给到您一个满意的价格",
]

DEFAULT_CONFIG = {
    "scripts": list(DEFAULT_SCRIPTS),
    "multiplier": 1.1,
    "quote_interval": 30,
    "detect_interval": 20,
    "auto_submit": True,
    "exclusions": [],
}


def clamp_float(value, default: float, lo: float, hi: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN
        return default
    return max(lo, min(hi, number))


def clamp_int(value, default: int, lo: int, hi: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, number))


def format_multiplier(value: float) -> str:
    return f"{value:g}"


def load_config() -> dict:
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    if not isinstance(raw, dict):
        return cfg

    scripts = raw.get("scripts")
    if isinstance(scripts, list):
        cfg["scripts"] = [str(item).strip() for item in scripts if str(item).strip()]

    exclusions = raw.get("exclusions")
    if isinstance(exclusions, list):
        cfg["exclusions"] = [str(item).strip() for item in exclusions if str(item).strip()]

    cfg["multiplier"] = clamp_float(raw.get("multiplier"), 1.1, 0.1, 10.0)
    cfg["quote_interval"] = clamp_int(raw.get("quote_interval"), 30, 1, 3600)
    cfg["detect_interval"] = clamp_int(raw.get("detect_interval"), 20, 1, 3600)
    cfg["auto_submit"] = bool(raw.get("auto_submit", True))
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )
