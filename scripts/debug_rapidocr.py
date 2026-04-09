from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
from rapidocr_onnxruntime import RapidOCR


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/debug_rapidocr.py <image>")
        return 1

    image_path = Path(sys.argv[1]).resolve()
    if not image_path.exists():
        print(f"image not found: {image_path}")
        return 1

    image = cv2.imread(str(image_path))
    engine = RapidOCR()
    result, _ = engine(image)
    payload = []
    for item in result or []:
        box, text, score = item
        payload.append({"text": text, "score": score, "box": box})
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
