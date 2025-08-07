#!/usr/bin/env python3
"""
Debug script to print the raw OpenAI response the VisionEngine receives so we can
see exactly what JSON (or not) the model returns. Useful for troubleshooting why
parsing fails or coordinates are wrong.
"""
import sys
import logging
from pathlib import Path
import pyautogui

sys.path.insert(0, str(Path(__file__).parent))

from relay.config import Config
from relay.core.vision_engine import VisionEngine, VisionContext


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    setup_logging()

    cfg = Config()
    api_key = cfg.get_openai_api_key()
    if not api_key:
        print("❌ Set OPENAI_API_KEY env var or in ~/.relay/config.json first.")
        return

    engine = VisionEngine(api_key=api_key, model=cfg.get("model", "o3-mini"))

    # Take a screenshot of current desktop
    screenshot = pyautogui.screenshot()

    context = VisionContext(
        task_description="Open Spotify application",
        previous_actions=[],
        screenshots_history=[],
        current_screenshot=""
    )

    # Build messages exactly as VisionEngine will
    screen_info = engine._get_screen_info()
    import base64, io
    buf = io.BytesIO(); screenshot.save(buf, format='PNG'); b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    messages = engine._build_context_messages(context, b64, screen_info)

    print("\n🔍 Prompt sent to model:\n-------------------------")
    for m in messages:
        if m["role"] == "system":
            print("[SYSTEM]\n" + m["content"][:1000] + "...\n")
        else:
            print("[USER] (truncated text + <image>)")
    print("-------------------------\n")

    print("⏳ Waiting for OpenAI response...\n")
    resp = engine.client.chat.completions.create(model=engine.model, messages=messages, max_tokens=800)

    raw = resp.choices[0].message.content
    print("🌐 Raw model response:\n-------------------------")
    print(raw)
    print("\n-------------------------")


if __name__ == "__main__":
    main()
