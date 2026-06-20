#!/usr/bin/env python3
"""PrivDNS Gateway 健康自检 —— 服务挂 / DNS 不应答 / 证书快到期时 Telegram 私信通知。
仅在「状态变化」时发(出问题发一次、恢复发一次), 不刷屏。由 pdg-health.timer 定时触发。
token / 允许 id / 证书路径 从 pdg-bot.service 读取, 不重复保存。
"""
import os, re, subprocess, json, sys

SVC = "/etc/systemd/system/pdg-bot.service"
STATE = "/opt/pdg-bot/health-state.json"

def _svc(k):
    try:
        m = re.search(rf"^Environment={k}=(.*)$", open(SVC).read(), re.M)
        return m.group(1).strip() if m else ""
    except Exception:  # noqa: BLE001
        return ""

os.environ.setdefault("PDG_BOT_TOKEN", _svc("PDG_BOT_TOKEN"))
os.environ.setdefault("PDG_CERT", _svc("PDG_CERT") or "/etc/mosdns/certs/fullchain.pem")
sys.path.insert(0, "/opt/pdg-bot")
import bot  # noqa: E402

ALLOWED = [int(x) for x in re.findall(r"\d+", _svc("PDG_BOT_ALLOWED"))]

def _active(s):
    return subprocess.run(["systemctl", "is-active", s], capture_output=True, text=True).stdout.strip() == "active"

def _dns_ok():
    r = subprocess.run(["dig", "+short", "+time=2", "+tries=1", "@127.0.0.1", "example.com", "A"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())

def _cert_expiring(days=14):
    r = subprocess.run(["openssl", "x509", "-checkend", str(days * 86400), "-noout", "-in", bot.CERT],
                       capture_output=True)
    return r.returncode != 0

def _check():
    p = []
    for s in ("mosdns", "sing-box", "pdg-bot", "pdg-probe81"):
        if not _active(s):
            p.append(f"❌ {s} 未运行")
    if _active("mosdns") and not _dns_ok():
        p.append("❌ mosdns 在跑但不应答 DNS")
    if os.path.exists(bot.CERT) and _cert_expiring(14):
        p.append("⚠️ DoT 证书 14 天内过期(查 certbot 续期)")
    return p

def _notify(text):
    for uid in ALLOWED:
        bot.post("sendMessage", {"chat_id": uid, "text": text, "parse_mode": "HTML",
                                 "disable_web_page_preview": True})

def main():
    if not os.environ.get("PDG_BOT_TOKEN") or not ALLOWED:
        return
    problems = _check()
    try:
        prev = json.load(open(STATE)).get("problems", [])
    except Exception:  # noqa: BLE001
        prev = []
    if problems and problems != prev:
        _notify("🚨 <b>PrivDNS Gateway 异常</b>\n" + "\n".join(problems) + "\n\n详情: <code>sudo pdg status</code>")
    elif not problems and prev:
        _notify("✅ <b>PrivDNS Gateway 已恢复正常</b>")
    try:
        json.dump({"problems": problems}, open(STATE, "w"))
    except Exception:  # noqa: BLE001
        pass

if __name__ == "__main__":
    main()
