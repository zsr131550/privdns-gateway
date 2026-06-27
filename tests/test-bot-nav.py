#!/usr/bin/env python3
"""Static regressions for Telegram bot navigation after operation results."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bot = (ROOT / "deploy/bot/pdg-bot.py").read_text(encoding="utf-8")

assert "OPS_BACK" in bot, "ops result keyboard must be explicit, not the full first-level MENU"
assert '"callback_data": "nav:ops"' in bot, "ops result keyboard should return to the ops submenu"
assert 'set_tfo(data == "tfo:on"); edit(chat, mid, msg if ok else ("❌ " + msg), OPS_BACK)' in bot, (
    "TFO toggle result must not show the whole first-level menu"
)
assert 'edit(chat, mid, "✅ 已重启 sing-box + mosdns" if ok else msg, OPS_BACK)' in bot, (
    "restart result must stay in ops navigation"
)
assert 'edit(chat, mid, (f"✅ geosite 已更新; 规则集刷新 {n} 个" if r.returncode == 0' in bot, (
    "rule-update result path should stay covered"
)
assert '), OPS_BACK); return' in bot, "rule-update result must use OPS_BACK"
