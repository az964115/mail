import time
import requests
from bs4 import BeautifulSoup
from config import MAIL_SERVER_URL, ADMIN_USER, ADMIN_PASS

session = requests.Session()
session.verify = False  # 內網自簽憑證

def login():
    url = f"{MAIL_SERVER_URL}/login.php"
    data = {
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }
    r = session.post(url, data=data)
    return r.status_code == 200


def search_quarantine(subject="", time_period="2"):
    url = f"{MAIL_SERVER_URL}/STaction.php"

    data = {
        "page": "ST",
        "op": "search",
        "mod": "search",
        "action": "list",

        "range": "12",              # 隔離郵件
        "time_period": time_period, # 2 = 本週（依你系統）

        "subject": subject,
        "pagesize": "50",
        "nowpage": "1",
    }

    r = session.post(url, data=data)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) >= 4:
            results.append({
                "mail_id": cols[0].find("input")["value"]
                            if cols[0].find("input") else "",
                "from": cols[1].get_text(strip=True),
                "to": cols[2].get_text(strip=True),
                "subject": cols[3].get_text(strip=True),
            })

    return results


def release_mail(mail_id):
    url = f"{MAIL_SERVER_URL}/STaction.php"

    data = {
        "op": "search",
        "action": "list",

        # 放行（重新投遞）
        "resend": "resend",
        "qmails_s[]": mail_id,

        "range": "12",
        "page": "ST",
    }

    r = session.post(url, data=data)
    r.raise_for_status()
    return True