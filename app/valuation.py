"""回收报价大厅数据解析与估值接口客户端。"""

from __future__ import annotations

import json
import re

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

API_URL = "http://47.104.224.59/api/quote"
# 估值服务凭据（由用户提供）
API_KEY = "dfk_GvcrbkvHce9MNzPI2Yy0OvUuyORbMQ"
PLATFORM = "crab"

_SECTION_STOP = (
    r"(?=\s*(?:近战武器|干员皮肤|红皮|行动等级|基础安全箱|进阶安全箱|"
    r"顶级安全箱|传说武器|史诗武器|哈夫币|总资产|流动资产|[】\]]|$))"
)


def _asset_millions(text: str, label: str) -> float | None:
    match = re.search(
        rf"{label}\s*[:：]\s*([0-9]+(?:\.[0-9]+)?)\s*([MmWw万亿]?)", text
    )
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit in ("万", "w", "W"):
        value /= 100.0
    elif unit == "亿":
        value *= 100.0
    return value


def _section_names(text: str, labels: tuple[str, ...]) -> list[str]:
    pattern = (
        rf"(?:{'|'.join(labels)})\s*[:：]\s*(?:\d+\s*个)?\s*(.*?){_SECTION_STOP}"
    )
    match = re.search(pattern, text)
    if not match:
        return []

    names = []
    for raw in re.split(r"[,，、;；]", match.group(1)):
        name = re.sub(r"\s+", "", raw)
        name = name.replace("-", "").replace("—", "").replace("·", "").replace("•", "")
        name = name.strip("：:。.")
        if name and name not in names:
            names.append(name)
    return names


def _cannot_second(text: str) -> bool:
    if any(word in text for word in ("不可二次", "不能二次", "无法二次", "不支持二次")):
        return True
    if "可二次" in text or "支持二次" in text:
        return False
    return True


def build_payload(item: dict) -> dict:
    title = str(item.get("title") or "")
    attrs = str(item.get("attrs") or "")
    remark = str(item.get("remark") or "")
    text = " ".join(part for part in (title, attrs, remark) if part)

    liquid = _asset_millions(text, "流动资产")
    total = _asset_millions(text, "总资产")
    liquid_m = liquid if liquid is not None else (total if total is not None else 0.0)

    return {
        "platform": PLATFORM,
        "liquidM": round(liquid_m, 2),
        "red": _section_names(text, ("干员皮肤", "红皮")),
        "knives": _section_names(text, ("近战武器",)),
        "gold": [],
        "bricks": [],
        "cannotSecond": _cannot_second(text),
        "manual": 0,
    }


def describe_payload(payload: dict, item: dict) -> str:
    parts = [
        f"流动资产 {payload['liquidM']:g}M",
        f"皮肤 {len(payload['red'])} 个",
        f"刀 {len(payload['knives'])} 把",
    ]
    goods_id = item.get("goodsId")
    if goods_id not in (None, ""):
        parts.append(f"ID {goods_id}")
    return " · ".join(parts)


class ValuationService(QObject):
    """串行调用估值接口，逐条把价格写入日志。"""

    log_message = Signal(str, str)
    busy_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._queue: list[tuple[int, dict, dict]] = []
        self._pending: tuple[int, dict, dict] | None = None
        self._success = 0
        self._failed = 0
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def estimate(self, items: list[dict], limit: int = 10):
        if self._busy:
            return
        targets = [item for item in items if isinstance(item, dict)][:limit]
        if not targets:
            return

        self._queue = [
            (index, item, build_payload(item))
            for index, item in enumerate(targets, 1)
        ]
        self._success = 0
        self._failed = 0
        self._busy = True
        self.busy_changed.emit(True)
        self._send_next()

    def _send_next(self):
        if not self._queue:
            self._busy = False
            kind = "ok" if self._failed == 0 else "muted"
            self.log_message.emit(
                f"估价完成 · 成功 {self._success} 条 / 失败 {self._failed} 条", kind
            )
            self.busy_changed.emit(False)
            return

        index, item, payload = self._queue.pop(0)
        self._pending = (index, item, payload)

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = QNetworkRequest(QUrl(API_URL))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        request.setRawHeader(b"X-API-Key", API_KEY.encode("ascii"))
        request.setTransferTimeout(20000)
        reply = self._manager.post(request, body)
        reply.finished.connect(lambda r=reply: self._on_reply(r))

    def _on_reply(self, reply):
        pending = self._pending
        self._pending = None
        if pending is None:
            reply.deleteLater()
            return

        index, item, payload = pending
        status = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )
        raw = bytes(reply.readAll()).decode("utf-8", "replace")
        network_error = reply.errorString()
        reply.deleteLater()

        data = {}
        try:
            if raw:
                data = json.loads(raw)
        except ValueError:
            data = {}

        price = data.get("price") if isinstance(data, dict) else None
        if (
            status == 200
            and isinstance(data, dict)
            and data.get("ok")
            and isinstance(price, (int, float))
        ):
            price_text = f"{price:g}" if isinstance(price, float) else str(price)
            self.log_message.emit(
                f"估价 #{index:02d} ¥{price_text} · "
                f"{describe_payload(payload, item)}",
                "ok",
            )
            self._success += 1
        else:
            reason = None
            if isinstance(data, dict):
                reason = data.get("error") or data.get("msg")
            if not reason:
                if status and status != 200:
                    reason = f"HTTP {status}"
                elif raw.strip():
                    reason = raw.strip()[:120]
                else:
                    reason = network_error or "无响应"
            self.log_message.emit(f"估价 #{index:02d} 失败：{reason}", "err")
            self._failed += 1

        self._send_next()
