#!/usr/bin/env bash

# Author: JDunphy - July 2025
#
# fail2ban-whitelist.sh
#
# Fetch Cloudflare’s current IPv4 & IPv6 ranges and, if they differ from the
# last saved copy, atomically replace the include file and reload Nginx.
#
# Purpose: we have a whitelist for fail2ban and this is our list of ip's that
#     should never be placed in jail.
#
# crontab example (run at 03:17 UTC daily):
# 17 3 * * * /usr/local/sbin/fail2ban-whitelist.sh >/dev/null 2>&1
#
# Caveat: Must change JAIL_CONFIG to match your jail or add it to jail.local
#
# %%%
# This should be in /etc/fail2ban/jail.local
#

#!/usr/bin/env bash
set -euo pipefail

JAIL_CONFIG="/etc/fail2ban/jail.d/nginx.conf"
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

curl -fsSL https://www.cloudflare.com/ips-v4 > "$tmp"
echo "" >> "$tmp"
curl -fsSL https://www.cloudflare.com/ips-v6 >> "$tmp"
echo "" >> "$tmp"
hostname -I | tr ' ' '\n' >> "$tmp"

# Clean up: remove empty lines, sort, and deduplicate
CLOUDFLARE_IPS=$(grep -v '^[[:space:]]*$' "$tmp" | sort -u | tr '\n' ' ' | sed 's/[[:space:]]*$//')

# Build complete ignore IP list
IGNORE_IPS="127.0.0.1/8 ::1 ${CLOUDFLARE_IPS}"

# Get current ignoreip line to compare
CURRENT_IGNORE=$(grep "^ignoreip = " "$JAIL_CONFIG" | cut -d'=' -f2- | sed 's/^ *//')

# Only update if different
if [ "$CURRENT_IGNORE" != "$IGNORE_IPS" ]; then
    echo "Updating ignoreip list..."
    
    # Create backup
    cp "$JAIL_CONFIG" "${JAIL_CONFIG}.bak"
    
    # Update the jail config
    sed -i "s|^ignoreip = .*|ignoreip = $IGNORE_IPS|" "$JAIL_CONFIG"
    
    # Test configuration before restarting
    if fail2ban-client -t; then
        echo "Configuration test passed. Restarting fail2ban..."
        #systemctl restart fail2ban
        s fail2ban-client restart
        echo "Updated successfully!"
    else
        echo "Configuration test failed! Restoring backup..."
        mv "${JAIL_CONFIG}.bak" "$JAIL_CONFIG"
        exit 1
    fi
else
    echo "No changes needed - ignoreip list is already up to date"
fi

# Show current status
echo "Current ignored IPs:"
s fail2ban-client get nginx ignoreip
