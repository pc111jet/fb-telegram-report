"""
Facebook Ads Manager -> Telegram күнделікті есеп боты
=======================================================

Бұл скрипт:
  1. Facebook Marketing API арқылы белгілі бір Ad Account-тың
     БҮГІНГІ статистикасын кампания (campaign) бойынша алады.
  2. Деректі оқуға ыңғайлы хабарламаға форматтайды.
  3. Telegram тобына жібереді.

Қажетті орта айнымалылары (environment variables):
  FB_ACCESS_TOKEN     - Facebook System User access token (ads_read рұқсатымен)
  FB_AD_ACCOUNT_ID    - "act_" префиксімен Ad Account ID (мысалы: act_1234567890)
  TELEGRAM_BOT_TOKEN  - BotFather берген бот токені
  TELEGRAM_CHAT_ID    - Telegram тобының chat_id-і (теріс сан, мысалы -1001234567890)

Қосымша баптау:
  DATE_PRESET         - "today" немесе "yesterday" (default: "today")
"""

import os
import sys
from datetime import datetime

import requests

# ============== БАПТАУЛАР ==============

FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
FB_AD_ACCOUNT_ID = os.environ.get("FB_AD_ACCOUNT_ID")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

FB_API_VERSION = "v19.0"
DATE_PRESET = os.environ.get("DATE_PRESET", "today")

# Лид/хабарласу саны үшін Facebook-тың action_type атаулары.
# Кампанияңыздың мақсатына (objective) байланысты осы тізімді
# толықтыру қажет болуы мүмкін:
#   - Messenger/WhatsApp хабарласу кампаниялары үшін:
#       "onsite_conversion.messaging_conversation_started_7d"
#   - Lead Forms (Instant Forms) кампаниялары үшін:
#       "lead", "leadgen.other", "onsite_conversion.lead_grouped"
LEAD_ACTION_TYPES = [
    "onsite_conversion.messaging_conversation_started_7d",
    "onsite_conversion.lead_grouped",
    "lead",
    "leadgen.other",
]


def check_config():
    missing = [
        name
        for name, val in [
            ("FB_ACCESS_TOKEN", FB_ACCESS_TOKEN),
            ("FB_AD_ACCOUNT_ID", FB_AD_ACCOUNT_ID),
            ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
            ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
        ]
        if not val
    ]
    if missing:
        print(f"Қате: мына орта айнымалылары орнатылмаған: {', '.join(missing)}")
        sys.exit(1)


def get_fb_insights():
    """Facebook Marketing API-ден кампания деңгейіндегі статистиканы алады."""
    url = f"https://graph.facebook.com/{FB_API_VERSION}/{FB_AD_ACCOUNT_ID}/insights"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "level": "campaign",
        "date_preset": DATE_PRESET,
        "fields": (
            "campaign_name,spend,impressions,reach,ctr,"
            "frequency,clicks,cpm,actions,cost_per_action_type"
        ),
        "limit": 200,
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print("Facebook API қатесі:", resp.text)
        resp.raise_for_status()
    return resp.json().get("data", [])


def extract_leads(campaign):
    """Кампаниядан лид/хабарласу санын және 1 лид құнын алады."""
    leads = 0
    cost_per_lead = None
    for action in campaign.get("actions", []):
        if action.get("action_type") in LEAD_ACTION_TYPES:
            leads += int(float(action.get("value", 0)))
    for cpa in campaign.get("cost_per_action_type", []):
        if cpa.get("action_type") in LEAD_ACTION_TYPES:
            cost_per_lead = float(cpa.get("value", 0))
    return leads, cost_per_lead


def fmt_money(value):
    return f"${value:,.2f}"


def format_message(campaigns):
    today = datetime.now().strftime("%d.%m.%Y")
    lines = [f"📊 *Facebook Ads есебі — {today}*", ""]

    total_spend = total_impr = total_reach = total_clicks = total_leads = 0

    for c in campaigns:
        name = c.get("campaign_name", "—")
        spend = float(c.get("spend", 0))
        impressions = int(c.get("impressions", 0))
        reach = int(c.get("reach", 0))
        ctr = float(c.get("ctr", 0))
        frequency = float(c.get("frequency", 0))
        clicks = int(c.get("clicks", 0))
        cpm = float(c.get("cpm", 0))
        leads, cost_per_lead = extract_leads(c)

        total_spend += spend
        total_impr += impressions
        total_reach += reach
        total_clicks += clicks
        total_leads += leads

        lines.append(f"🔹 *{name}*")
        lines.append(f"   👤 Жазған адам (лид): {leads}")
        if cost_per_lead is not None:
            lines.append(f"   💵 1 лид құны: {fmt_money(cost_per_lead)}")
        lines.append(f"   💰 Бюджет (spend): {fmt_money(spend)}")
        lines.append(f"   👁 Показ (impressions): {impressions:,}")
        lines.append(f"   📡 Қамту (reach): {reach:,}")
        lines.append(f"   📈 CTR: {ctr:.2f}%")
        lines.append(f"   🔁 Частота (frequency): {frequency:.2f}")
        lines.append(f"   🖱 Клик (clicks): {clicks:,}")
        lines.append(f"   📐 CPM: {fmt_money(cpm)}")
        lines.append("")

    lines.append("———————————————")
    lines.append("*Барлығы (барлық кампания бойынша):*")
    lines.append(f"👤 Жалпы лид: {total_leads}")
    if total_leads:
        lines.append(f"💵 Орташа 1 лид: {fmt_money(total_spend / total_leads)}")
    lines.append(f"💰 Жалпы бюджет: {fmt_money(total_spend)}")
    lines.append(f"👁 Жалпы показ: {total_impr:,}")
    lines.append(f"📡 Жалпы қамту: {total_reach:,}")
    lines.append(f"🖱 Жалпы клик: {total_clicks:,}")

    return "\n".join(lines)


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code != 200:
        print("Telegram API қатесі:", resp.text)
        resp.raise_for_status()


def main():
    check_config()
    campaigns = get_fb_insights()

    if not campaigns:
        send_telegram_message(
            f"⚠️ {datetime.now().strftime('%d.%m.%Y')} күніне активті "
            f"кампания табылмады немесе деректер әлі жоқ."
        )
        print("Активті кампания табылмады.")
        return

    message = format_message(campaigns)
    send_telegram_message(message)
    print("Хабарлама сәтті жіберілді.")


if __name__ == "__main__":
    main()
