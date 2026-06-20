#!/usr/bin/env bash
# 自动识别「内网卡来源段」: 抓包看哪个私有网段(10/172.16-31/192.168)从内网卡打到本机, 推断成 /16。
# 用法: detect-internal-range.sh [抓包秒数] [本机公网IP(仅用于提示)]
# 成功: stdout 打印 CIDR (如 172.22.0.0/16) 并 exit 0; 失败: 空输出 exit 1。
set -uo pipefail
DUR="${1:-40}"
SERVER_IP="${2:-本机公网IP}"

command -v tcpdump >/dev/null 2>&1 || { echo "" ; exit 1; }

cat >&2 <<EOF
──────────────────────────────────────────────
 正在抓包识别内网卡网段, 持续约 ${DUR} 秒。
 请现在用手机(确保走【内网卡/蜂窝】, 不要走 WiFi)做任意一件:
   • 浏览器打开  http://${SERVER_IP}
   • 或 在能 ping 的工具里 ping ${SERVER_IP}
 (只要有一个包从内网卡打到本机即可)
──────────────────────────────────────────────
EOF

src=$(timeout "$DUR" tcpdump -ni any -c 40 \
        '(tcp[tcpflags] & tcp-syn != 0 or icmp) and (net 10.0.0.0/8 or net 172.16.0.0/12 or net 192.168.0.0/16)' \
        2>/dev/null \
      | grep -oE '(10|172|192)\.[0-9]+\.[0-9]+\.[0-9]+' \
      | grep -vE '\.(255|0)$' \
      | sort | uniq -c | sort -rn | awk 'NR==1{print $2}')

[[ -z "$src" ]] && { echo ""; exit 1; }
# 取前两段当 /16 (内网卡通常是一个 /16 或更大的运营商私网段)
echo "$src" | awk -F. '{print $1"."$2".0.0/16"}'
