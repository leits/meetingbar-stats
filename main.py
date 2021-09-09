import os
import requests
from loguru import logger

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass

from deta import app

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
    github_stats = get_github_stats()
    patreon_stats = get_patreon_stats()

    message = (
        "MeetingBar\n"
        f"⭐{github_stats['stargazers']}"
        f"📥{github_stats['downloads']}"
        "\n"
        f"🦸{patreon_stats['patron_count']}"
        f"${patreon_stats['pledge_sum']}"
    )

    send(message)
    logger.info("END")
    return "Success"


if __name__ == "__main__":
    main()
