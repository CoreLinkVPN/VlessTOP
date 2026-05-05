import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import base64
import socket
import random
import urllib.parse
import requests

FRIEND_SUBS = [x.strip() for x in os.getenv("FRIEND_SUBS", "").split(",") if x.strip()]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_FILE = os.getenv("GITHUB_FILE", "sub.txt")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

MAX_SERVERS = int(os.getenv("MAX_SERVERS", "26"))
TIMEOUT = 3

def decode_sub(text):
    try:
        decoded = base64.b64decode(text + "=" * (-len(text) % 4)).decode("utf-8")
        if "vless://" in decoded:
            return decoded
    except:
        pass
    return text

def extract_vless(text):
    text = decode_sub(text)
    return [x.strip() for x in text.splitlines() if x.strip().startswith("vless://")]

def get_host(link):
    try:
        u = urllib.parse.urlparse(link)
        return u.hostname
    except:
        return None

def is_alive(link):
    try:
        host = get_host(link)
        port = urllib.parse.urlparse(link).port or 443
        with socket.create_connection((host, port), timeout=TIMEOUT):
            return True
    except:
        return False

def get_flag(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=3).json()
        code = r.get("countryCode", "UN")
        return ''.join([chr(127397 + ord(c)) for c in code])
    except:
        return "🏳️"

def rename(link, index):
    clean = link.split("#")[0]
    host = get_host(link)

    flag = get_flag(host) if host else "🏳️"

    name = f"{flag} {os.getenv('PREFIX', 'SkyWhy/CoreLink | Node')} {index}"
    return clean + "#" + urllib.parse.quote(name)

def upload(content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    r = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH})
    sha = r.json().get("sha") if r.status_code == 200 else None

    data = {
        "message": "update subscription",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": GITHUB_BRANCH,
    }

    if sha:
        data["sha"] = sha

    requests.put(url, headers=headers, json=data).raise_for_status()

def main():
    all_links = []

    for sub in FRIEND_SUBS:
        try:
            text = requests.get(sub, timeout=10).text
            all_links += extract_vless(text)
        except:
            pass

    all_links = list(dict.fromkeys(all_links))
    random.shuffle(all_links)

    good = []

    for link in all_links:
        if is_alive(link):
            good.append(link)
        if len(good) >= MAX_SERVERS:
            break

    final = []
    for i, link in enumerate(good, 1):
        final.append(rename(link, i))

    upload("\n".join(final))

    print(f"Готово: {len(final)} серверов")

if __name__ == "__main__":
    main()
