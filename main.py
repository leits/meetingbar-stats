import os
import json
import requests
from loguru import logger
import resend

from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM")
RESEND_TO = os.getenv("RESEND_TO")

STATS_FILE = "stats.json"


def load_prev_stats() -> dict:
    if os.path.isfile(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {
        "github": {"stargazers": 0, "downloads": 0},
        "patreon": {"patron_count": 0, "pledge_sum": 0},
    }


def save_stats(stats: dict):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def get_github_stats() -> dict:
    repo_url = "https://api.github.com/repos/leits/MeetingBar"

    # Stargazers count
    resp = requests.get(repo_url)
    repo_stats = resp.json()
    stargazers_count = repo_stats["stargazers_count"]

    # Download count
    resp = requests.get(f"{repo_url}/releases?per_page=100")
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


def send_via_resend(html_content):
    resend.api_key = RESEND_API_KEY
    response = resend.Emails.send(
        {
            "from": RESEND_FROM,
            "to": RESEND_TO,
            "subject": "Monthly MeetingBar Stats",
            "html": html_content,
        }
    )
    logger.info(f"Email sent, id={response.get('id')}")


def build_html(stats, prev_stats):
    html = f"""
    <h2>Monthly MeetingBar Stats</h2>
    <ul>
      <li>⭐ Stars: {stats['github']['stargazers']} ({stats['github']['stargazers'] - prev_stats['github']['stargazers']:+})</li>
      <li>📥 Downloads: {stats['github']['downloads']} ({stats['github']['downloads'] - prev_stats['github']['downloads']:+})</li>
      <li>🦸 Patrons: {stats['patreon']['patron_count']} ({stats['patreon']['patron_count'] - prev_stats['patreon']['patron_count']:+})</li>
      <li>💸 Pledge: ${stats['patreon']['pledge_sum']} ({stats['patreon']['pledge_sum'] - prev_stats['patreon']['pledge_sum']:+})</li>
    </ul>
    """
    return html


# @app.lib.run()
# @app.lib.cron()
def main(event=None) -> str:
    logger.info("START")
    prev_stats = load_prev_stats()

    stats = {"github": get_github_stats(), "patreon": get_patreon_stats()}

    html = build_html(stats, prev_stats)
    send_via_resend(html)

    save_stats(stats)

    print(html)
    logger.info("SENT")
    return "Success"


if __name__ == "__main__":
    main()
