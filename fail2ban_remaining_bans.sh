#!/bin/bash

# Author: JDunphy - July 2025
#
# Caveat: must be run as root or required permissions for fail2ban.sqlite3
#
# Sample Output:
#
#   nginx        13.74.177.16    2025-07-12 19:27:28  2025-07-12 20:27:28  165      (00:02:45)
#   nginx        157.245.36.108  2025-07-12 13:12:54  2025-07-12 21:12:54  2891     (00:48:11)
#   nginx        2602:fb54:372:: 2025-07-12 19:32:11  2025-07-12 20:32:11  448      (00:07:28)
#   nginx        5.175.234.102   2025-07-12 19:59:24  2025-07-12 20:59:24  2081     (00:34:41)
#
#

DB="/var/lib/fail2ban/fail2ban.sqlite3"
now_epoch=$(date +%s)

sqlite3 "$DB" <<EOF | awk -F'|' -v now="$now_epoch" '
  {
    remaining = $4 + $3 - now
    if (remaining > 0) {
      printf "%-12s %-15s %-20s %-20s %-8d %s\n", $1, $2, $5, $6, remaining, "(" strftime("%H:%M:%S", remaining, 1) ")"
    }
  }
' | sort -nk5
SELECT 
  jail, 
  ip, 
  timeofban, 
  bantime, 
  datetime(timeofban, 'unixepoch') as banned_at, 
  datetime(timeofban + bantime, 'unixepoch') as expires_at
FROM bans;
EOF

