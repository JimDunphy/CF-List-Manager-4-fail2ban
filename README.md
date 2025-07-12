
# Cloudflare IP List Manager

A Python script to add, delete, or list IP addresses in a [Cloudflare Custom IP List](https://developers.cloudflare.com/api/resources/rules/subresources/lists/) using the Cloudflare API. This is particularly useful when integrated with **Fail2Ban** as a custom action to dynamically manage malicious IPs.

---

## ✨ Features

- Add or delete IPs to/from a specific Cloudflare list (e.g., `block`, `challenge`, `bots`)
- View the current list contents
- Supports optional comments
- Can be integrated with Fail2Ban for automated IP blocking

---

## 📦 Requirements

To use this tool effectively, the following setup is required:

1. **Cloudflare Proxy Enabled** – Your domain must be proxied through Cloudflare (orange cloud enabled).
2. **Origin Firewall Rules** – Your origin server’s firewall must be configured to allow **only** Cloudflare IPs and block all direct traffic.
3. **Pre-Created IP List** – You must have already created one or more Cloudflare IP Lists under **Account → Configurations → Lists**.
4. **Associated Firewall Rules** – You must have firewall rules configured to act on these lists. For example, you can block or challenge IPs that are on a specific list when they access your site via Cloudflare.
5. **Cloudflare Lists** – These are account wide with CF and even the free accounts can create custom lists [limit](https://developers.cloudflare.com/waf/tools/lists/#availability)

You will also need:

- Python 3.x
- `requests` module (`pip install requests`)
- A Cloudflare API token with permission to manage Lists
- Your Cloudflare Account ID and Zone ID

---

## 🔧 Configuration

Edit the `USER-SPECIFIC SETTINGS` section in the script to define:

```python
CF_API_TOKEN = 'your_api_token'
CF_ACCOUNT_ID = 'your_account_id'
CF_ZONE_ID = 'your_zone_id'
LIST_IDS = {
    'block': 'your_block_list_id',
    'challenge': 'your_challenge_list_id',
    'bots': 'your_bots_list_id'
}
```

---

## 🚀 Usage

Make the script executable:

```bash
chmod +x modifyBanList.py
```

Then run:

### Add IP

```bash
./modifyBanList.py <ip> add
```

Example:

```bash
./modifyBanList.py 203.0.113.4 add
```

### Add IP with comment

```bash
./modifyBanList.py <ip> add --comment "Port scan detected"
```

### Add IP to specific list

```bash
./modifyBanList.py <ip> add --list-name bots
```

### Delete IP

```bash
./modifyBanList.py <ip> del
```

### Delete IP from specific list

```bash
./modifyBanList.py <ip> del --list-name challenge
```

### View current entries in a list

```bash
./modifyBanList.py --list --list-name block
```

---

## 🛡️ Fail2Ban Integration

Create a custom action file:  
`/etc/fail2ban/action.d/cloudflarelist.conf`

```ini
[Definition]
actionstart =
actionstop =
actioncheck =
actionban = /path/to/modifyBanList.py <ip> add --comment "Banned by Fail2Ban"
actionunban = /path/to/modifyBanList.py <ip> del

[Init]
```

Replace `/path/to/modifyBanList.py` with the actual full path.

Then in your jail config (e.g., `/etc/fail2ban/jail.d/nginx-bots.conf`):

```ini
[nginx-bots]
enabled = true
filter = nginx-bad-bots
action = cloudflarelist
logpath = /var/log/nginx/access.log
findtime = 600
bantime = 3600
maxretry = 5
```

---

## 🔗 Cloudflare API Resources

- [Custom Lists](https://developers.cloudflare.com/waf/tools/lists/custom-lists/)
- [List Lists](https://developers.cloudflare.com/api/resources/rules/subresources/lists/)
- [List Items](https://developers.cloudflare.com/api/resources/rules/subresources/lists/subresources/items/)
- [Add Items](https://developers.cloudflare.com/api/resources/rules/subresources/lists/subresources/items/methods/create/)
- [Remove Items](https://developers.cloudflare.com/api/resources/rules/subresources/lists/subresources/items/methods/delete/)
- [API Tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)

---

## 🧪 Debugging

Run with `--debug` to print more verbose output:

```bash
./modifyBanList.py <ip> add --debug
```

---

## 📜 License

MIT
