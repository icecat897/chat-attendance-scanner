from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from rapidocr_onnxruntime import RapidOCR


BASE_DIR = Path(__file__).resolve().parent
MEMBERS_PATH = BASE_DIR / "成员.md"
DATA_DIR = BASE_DIR / "data"
MAPPINGS_PATH = DATA_DIR / "mappings.json"
OCR_ENGINE = RapidOCR()


def ensure_data_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not MAPPINGS_PATH.exists():
        MAPPINGS_PATH.write_text("{}\n", encoding="utf-8")


def normalize_text(value: str) -> str:
    value = re.sub(r"\s+", "", value)
    value = value.replace("（", "(").replace("）", ")")
    return value.strip()


def chinese_only(value: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", normalize_text(value)))


def edit_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            substitution_cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + substitution_cost,
                )
            )
        previous = current
    return previous[-1]


def best_name_distance(raw_name: str, member_name: str) -> int:
    raw_text = chinese_only(raw_name)
    member_text = chinese_only(member_name)
    if not raw_text or not member_text:
        return 99
    if member_text in raw_text:
        return 0

    lengths = {len(member_text)}
    if len(member_text) > 2:
        lengths.add(len(member_text) - 1)
    lengths.add(len(member_text) + 1)

    candidates: list[str] = []
    for length in sorted(lengths):
        if length <= 0 or length > len(raw_text):
            continue
        for index in range(0, len(raw_text) - length + 1):
            candidates.append(raw_text[index : index + length])

    if not candidates:
        candidates = [raw_text]

    return min(edit_distance(candidate, member_text) for candidate in candidates)


def load_members() -> tuple[list[str], set[str]]:
    if not MEMBERS_PATH.exists():
        raise HTTPException(status_code=500, detail="未找到 成员.md")

    members: list[str] = []
    leaders: set[str] = set()
    for raw_line in MEMBERS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        cleaned = re.sub(r"^\d+\.\s*", "", line)
        is_leader = "（组长）" in cleaned or "(组长)" in cleaned
        name = cleaned.replace("（组长）", "").replace("(组长)", "").strip()
        if not name:
            continue
        members.append(name)
        if is_leader:
            leaders.add(name)

    return members, leaders


def load_mappings() -> dict[str, str]:
    ensure_data_files()
    try:
        content = json.loads(MAPPINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"映射文件损坏: {exc}") from exc

    if not isinstance(content, dict):
        raise HTTPException(status_code=500, detail="映射文件格式错误")

    cleaned: dict[str, str] = {}
    for key, value in content.items():
        if isinstance(key, str) and isinstance(value, str):
            cleaned[key] = value
    return cleaned


def save_mappings(mappings: dict[str, str]) -> None:
    ensure_data_files()
    MAPPINGS_PATH.write_text(
        json.dumps(dict(sorted(mappings.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_leave_names(value: str) -> list[str]:
    if not value.strip():
        return []

    tokens = re.split(r"[，,、\n\r;；\s]+", value)
    return [item for item in (token.strip() for token in tokens) if item]


def candidate_members(raw_name: str, members: list[str]) -> list[str]:
    normalized_raw = normalize_text(raw_name)
    exact_matches = [member for member in members if normalized_raw == normalize_text(member)]
    if exact_matches:
        return exact_matches

    substring_matches = [
        member for member in members if normalize_text(member) and normalize_text(member) in normalized_raw
    ]
    if substring_matches:
        substring_matches.sort(key=len, reverse=True)
        return substring_matches

    fuzzy_matches: list[str] = []
    for member in members:
        distance = best_name_distance(raw_name, member)
        if distance <= 1:
            fuzzy_matches.append(member)

    if len(fuzzy_matches) == 1:
        return fuzzy_matches

    return []


def resolve_sender(
    raw_name: str,
    members: list[str],
    mappings: dict[str, str],
    member_hint: str | None = None,
) -> dict[str, Any]:
    raw_name = raw_name.strip()
    if member_hint and member_hint in members:
        return {
            "status": "hint_matched",
            "member": member_hint,
            "candidates": [member_hint],
            "raw_name": raw_name,
        }

    mapped = mappings.get(raw_name)
    if mapped:
        return {"status": "mapped", "member": mapped, "candidates": [mapped], "raw_name": raw_name}

    candidates = candidate_members(raw_name, members)
    if len(candidates) == 1:
        return {
            "status": "auto_matched",
            "member": candidates[0],
            "candidates": candidates,
            "raw_name": raw_name,
        }

    return {"status": "unresolved", "member": None, "candidates": candidates, "raw_name": raw_name}


class DetectedSender(BaseModel):
    raw_name: str = Field(min_length=1)
    source: str = ""
    confidence: float | None = None
    member_hint: str | None = None


class AnalyzeRequest(BaseModel):
    detected_senders: list[DetectedSender]
    leave_names: str = ""
    manual_present_members: list[str] = []


class MappingRequest(BaseModel):
    raw_name: str = Field(min_length=1)
    member_name: str = Field(min_length=1)


def image_bytes_to_cv2(content: bytes) -> np.ndarray:
    array = np.frombuffer(content, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="图片读取失败")
    return image


def ocr_detect_senders(image: np.ndarray, source: str) -> list[dict[str, Any]]:
    result, _ = OCR_ENGINE(image)
    detections: list[dict[str, Any]] = []
    for item in result or []:
        box, text, score = item
        raw_name = str(text).strip()
        if len(chinese_only(raw_name)) < 2:
            continue
        detections.append(
            {
                "raw_name": raw_name,
                "source": source,
                "confidence": float(score),
                "member_hint": None,
            }
        )
    return detections


def dedupe_detected_senders(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for item in items:
        key = normalize_text(item["raw_name"])
        existing = latest.get(key)
        if existing is None or item.get("confidence", 0) > existing.get("confidence", 0):
            latest[key] = item
    return list(latest.values())


ensure_data_files()
app = FastAPI(title="聊天图片签到统计")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    members, leaders = load_members()
    return {
        "members": members,
        "leaders": sorted(leaders),
        "mappings": load_mappings(),
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    members, leaders = load_members()
    mappings = load_mappings()
    leave_names = parse_leave_names(request.leave_names)
    excluded = set(leaders) | set(leave_names)
    active_members = [member for member in members if member not in excluded]

    present_members: set[str] = set()
    unresolved_entries: list[dict[str, Any]] = []
    recognized_details: list[dict[str, Any]] = []
    seen_unresolved: set[str] = set()

    for entry in request.detected_senders:
        resolved = resolve_sender(entry.raw_name, members, mappings, member_hint=entry.member_hint)
        if resolved["member"] and resolved["member"] not in excluded:
            present_members.add(resolved["member"])

        detail = {
            "raw_name": entry.raw_name,
            "source": entry.source,
            "confidence": entry.confidence,
            "member_hint": entry.member_hint,
            **resolved,
        }
        recognized_details.append(detail)

        if resolved["status"] == "unresolved" and entry.raw_name not in seen_unresolved:
            seen_unresolved.add(entry.raw_name)
            unresolved_entries.append(
                {
                    "raw_name": entry.raw_name,
                    "candidates": resolved["candidates"],
                }
            )

    manual_present_members = sorted({name for name in request.manual_present_members if name in active_members})
    for name in manual_present_members:
        present_members.add(name)

    for name in manual_present_members:
        recognized_details.append(
            {
                "raw_name": name,
                "source": "manual_review",
                "confidence": 100,
                "member_hint": name,
                "status": "manual_confirmed",
                "member": name,
                "candidates": [name],
            }
        )

    missing_members = sorted(member for member in active_members if member not in present_members)

    return {
        "present_members": sorted(present_members),
        "missing_members": missing_members,
        "excluded_members": sorted(excluded),
        "leave_members": leave_names,
        "leaders": sorted(leaders),
        "unresolved": unresolved_entries,
        "recognized_details": recognized_details,
        "manual_present_members": manual_present_members,
        "active_count": len(active_members),
        "present_count": len(present_members),
        "missing_count": len(missing_members),
    }


@app.post("/api/scan")
async def scan_images(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    detected_senders: list[dict[str, Any]] = []
    for upload in files:
        content = await upload.read()
        if not content:
            continue
        image = image_bytes_to_cv2(content)
        detected_senders.extend(ocr_detect_senders(image, upload.filename or "upload"))

    return {
        "detected_senders": dedupe_detected_senders(detected_senders),
        "count": len(detected_senders),
    }


@app.post("/api/mappings")
def upsert_mapping(request: MappingRequest) -> dict[str, Any]:
    members, _ = load_members()
    if request.member_name not in members:
        raise HTTPException(status_code=400, detail="映射目标不在成员名单中")

    mappings = load_mappings()
    mappings[request.raw_name.strip()] = request.member_name.strip()
    save_mappings(mappings)
    return {"ok": True, "mappings": mappings}


@app.get("/api/mappings")
def get_mappings() -> dict[str, str]:
    return load_mappings()
