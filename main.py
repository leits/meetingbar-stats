import os
import requests
from loguru import logger

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass

from deta import app, Deta

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_github_stats() -> dict:
    repo_url = "https://api.github.com/repos/leits/MeetingBar"

    # Stargazers count
    resp = requests.get(repo_url)
    repo_stats = resp.json()
    stargazers_count = repo_stats["stargazers_count"]

    # Download count
    resp = requests.get(f"{repo_url}/releases")
    releases = resp.json()

    download_count = 0
    for release in releases:
        download_count += sum([asset["download_count"] for asset in release["assets"]])

    github_stats = {
        "stargazers": stargazers_count,
        "downloads": download_count,
    }

    logger.info(f"Collected github data")
    return github_stats


def get_patreon_stats() -> dict:
    resp = requests.get("https://www.patreon.com/api/campaigns/4672520")
    resp_json = resp.json()

    patreon_stats = {
        "patron_count": resp_json["data"]["attributes"]["patron_count"],
        "pledge_sum": int(resp_json["data"]["attributes"]["pledge_sum"] / 100),
    }

    logger.info(f"Collected patreon data")
    return patreon_stats


def send(message):
    url = "https://api.telegram.org/bot{}/sendMessage".format(TOKEN)

    payload = {
        "text": message,
        "chat_id": CHAT_ID,
        "parse_mode": "markdown",
    }
    requests.post(url, data=payload)
    logger.info(f"Sent message to telegram")


@app.lib.run()
@app.lib.cron()
def main(event=None) -> str:
    logger.info("START")
    stats = {"github": get_github_stats(), "patreon": get_patreon_stats()}

    deta = Deta()
    db = deta.Base("stats")
    prev_stats = db.get("meetingbar")
    db.put(stats, "meetingbar")

    message = (
        "MeetingBar\n"
        f"⭐{stats['github']['stargazers']} ({stats['github']['stargazers'] - prev_stats['github']['stargazers']:+})\n"
        f"📥{stats['github']['downloads']} ({stats['github']['downloads'] - prev_stats['github']['downloads']:+})\n"
        f"🦸{stats['patreon']['patron_count']} ({stats['patreon']['patron_count'] - prev_stats['patreon']['patron_count']:+})\n"
        f"💸 ${stats['patreon']['pledge_sum']} ({stats['patreon']['pledge_sum'] - prev_stats['patreon']['pledge_sum']:+})\n"
    )

    send(message)
    logger.info("SENT")
    return "Success"


if __name__ == "__main__":
    main()
