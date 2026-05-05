# --- FIX UTF-8 ---
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import base64
import socket
import random
import urllib.parse
import requests

# --- ENV ---
FRIEND_SUBS = [x.strip() for x in os.getenv("FRIEND_SUBS", "").split(",") if x.strip()]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_FILE = os.getenv("GITHUB_FILE", "sub.txt")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

PREFIX = os.getenv("PREFIX", "LTE")
MAX_SERVERS = int(os.getenv("MAX_SERVERS", "50"))
TIMEOUT = int(os.getenv("TIMEOUT", "3"))

PROFILE_TITLE = os.getenv("PROFILE_TITLE", "LTE VPN")
PROFILE_WEB_PAGE_URL = os.getenv("PROFILE_WEB_PAGE_URL", "")
SUPPORT_URL = os.getenv("SUPPORT_URL", "")
ANNOUNCE = os.getenv("ANNOUNCE", "Проверяйте доступность серверов ⏱️ Ping Test")
UPDATE_INTERVAL = os.getenv("UPDATE_INTERVAL", "1")
EXPIRE = os.getenv("EXPIRE", "55556057600")


# --- FUNCTIONS ---
def decode_sub(text):
    text = text.strip()
    try:
        decoded = base64.b64decode(text + "=" * (-len(text) % 4)).decode("utf-8")
        if "vless://" in decoded:
            return decoded
    except Exception:
        pass
    return text


def extract_vless(text):
    text = decode_sub(text)
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("vless://")
    ]


def is_alive(link):
    try:
        u = urllib.parse.urlparse(link)
        host = u.hostname
        port = u.port or 443

        if not host:
            return False

        with socket.create_connection((host, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False


def rename(link, name):
    clean = link.split("#")[0]
    return clean + "#" + urllib.parse.quote(name)


def build_header():
    return f"""#profile-title: {PROFILE_TITLE}
#profile-update-interval: {UPDATE_INTERVAL}
#profile-web-page-url: {PROFILE_WEB_PAGE_URL}
#support-url: {SUPPORT_URL}
#announce: {ANNOUNCE}
#subscription-userinfo: upload=0; download=0; total=0; expire={EXPIRE}

"""


def upload_to_github(content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    # Проверяем есть ли файл
    r = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH})
    sha = r.json().get("sha") if r.status_code == 200 else None

    data = {
        "message": "update subscription",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": GITHUB_BRANCH,
    }

    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, json=data)
    r.raise_for_status()


# --- MAIN ---
def main():
    all_links = []

    for sub_url in FRIEND_SUBS:
        try:
            text = requests.get(sub_url, timeout=20).text
            all_links.extend(extract_vless(text))
        except Exception:
            continue

    # убираем дубли
    all_links = list(dict.fromkeys(all_links))
    random.shuffle(all_links)

    good = []

    for link in all_links:
        if is_alive(link):
            good.append(rename(link, f"{PREFIX} | {len(good) + 1}"))

        if len(good) >= MAX_SERVERS:
            break

    final_sub = build_header() + "\n".join(good)
    upload_to_github(final_sub)

    print(f"Готово. Серверов: {len(good)}")


if __name__ == "__main__":
    main()
