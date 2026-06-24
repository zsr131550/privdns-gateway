#!/usr/bin/env python3
"""parse_link 回归: 各类代理链接 + Surge ss 行 → 正确 sing-box 出站 dict。纯 stdlib, CI 可跑。"""
import base64
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("pdgbot", os.path.join(ROOT, "deploy/bot/pdg-bot.py"))
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except SystemExit:
    pass

fails = 0


def check(name, got, **want):
    global fails
    bad = {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}
    if bad:
        print("[FAIL]", name, bad); fails += 1
    else:
        print("[OK]  ", name)


# Surge ss 行(SS2022 + tfo + udp-relay)
check("Surge ss 行",
      m.parse_link('🇭🇰 X = ss, 1.2.3.4, 11111, encrypt-method=2022-blake3-aes-128-gcm, '
                   'password="ab+C/9==", tfo=true, udp-relay=true'),
      type="shadowsocks", server="1.2.3.4", server_port=11111,
      method="2022-blake3-aes-128-gcm", password="ab+C/9==", tcp_fast_open=True)

# ss:// SIP002 (method:password 经 base64url)
ui = base64.urlsafe_b64encode(b"aes-256-gcm:pass123").decode().rstrip("=")
check("ss:// (b64 用户信息)", m.parse_link("ss://%s@5.6.7.8:8388#name" % ui),
      type="shadowsocks", server="5.6.7.8", server_port=8388, method="aes-256-gcm", password="pass123")

# 非法输入应报错
try:
    m.parse_link("garbage no scheme")
    print("[FAIL] 非法输入未报错"); fails += 1
except ValueError:
    print("[OK]   非法输入正确报错")

print("─" * 40)
print("失败 %d" % fails)
sys.exit(1 if fails else 0)
