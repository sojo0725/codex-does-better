#!/usr/bin/env python3
"""Stop hook for the codex-does-better skill.

When Claude's final reply hedges ("應該是", "我猜", "probably" ...), block the
stop once and send it back to check, using the codex-does-better skill.

Bare 「可能」 is deliberately not on the list: it shows up in almost every
long reply ("可能的原因", "不可能"), and blocking on it would cost an extra
turn nearly every time.

Never blocks twice in a row (stop_hook_active), and never blocks a reply that
already went through the skill (it carries the taunt line).
"""
import json
import re
import sys

HEDGES = [
    "應該是", "可能是", "大概是", "我不確定", "不太確定", "我猜", "印象中", "我記得",
    "probably", "i think", "i believe", "not sure", "if i recall",
]
TAUNT = "Codex 都比你強，要你何用？"


def without_quoted(text):
    """Drop code, quotes and blockquotes: hedge words there are being cited, not used."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"「[^」]*」|『[^』]*』|“[^”]*”", " ", text)
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">"))


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if payload.get("stop_hook_active"):
        return
    reply = payload.get("last_assistant_message") or ""
    if not reply or TAUNT in reply:
        return
    plain = without_quoted(reply).lower()
    hits = [h for h in HEDGES if h in plain]
    if not hits:
        return
    words = "、".join(f"「{h}」" for h in hits[:3])
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"你的回覆用了{words}這類不確定的說法。{TAUNT}\n"
            "用 codex-does-better skill 處理：查得到的就去查，查完照它的格式重新回答。"
            "如果是查不到的事，或只是給建議時正常的保留語氣，也照格式說明為什麼還不確定，"
            "不要為了過關硬改成肯定句。"
        ),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
