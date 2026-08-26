import os
import re
import time
import requests

# =========================================================
# Telegram Bot Token
# Render 환경변수에서 가져옴
# =========================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN 환경변수가 설정되지 않았습니다.")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 무료 환율 API
EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"


# =========================================================
# 텔레그램 메시지 보내기
# =========================================================
def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=15
        )
    except Exception as e:
        print("메시지 전송 오류:", e)


# =========================================================
# 환율 가져오기
# =========================================================
def get_rates():
    response = requests.get(
        EXCHANGE_API,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    if data.get("result") != "success":
        raise Exception("환율 API 오류")

    return data["rates"]


# =========================================================
# 숫자 추출
# 예:
# 100달러 → 100
# 1,000 달러 → 1000
# =========================================================
def extract_amount(text):
    match = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)", text)

    if match:
        return float(match.group(1).replace(",", ""))

    return 1


# =========================================================
# 환율 표시
# =========================================================
def exchange_message():
    rates = get_rates()

    usd_krw = rates["KRW"]
    usd_jpy = rates["JPY"]
    usd_eur = rates["EUR"]
    usd_cny = rates["CNY"]

    # USD 기준 환율을 이용해 계산
    jpy_krw = usd_krw / usd_jpy
    eur_krw = usd_krw / usd_eur
    cny_krw = usd_krw / usd_cny

    message = (
        "💱 환율 정보\n"
        "━━━━━━━━━━━━━━\n\n"

        f"🇺🇸 1 USD = {usd_krw:,.2f} KRW\n"
        f"🇯🇵 100 JPY = {jpy_krw * 100:,.2f} KRW\n"
        f"🇪🇺 1 EUR = {eur_krw:,.2f} KRW\n"
        f"🇨🇳 1 CNY = {cny_krw:,.2f} KRW\n\n"

        "━━━━━━━━━━━━━━\n"
        "📌 기준: USD 기준 환율\n"
        "※ 환율 API 최신 제공값 기준"
    )

    return message


# =========================================================
# 특정 통화 계산
# =========================================================
def convert_currency(text):

    rates = get_rates()

    amount = extract_amount(text)

    # 달러
    if "달러" in text or "usd" in text.lower():
        krw = amount * rates["KRW"]

        return (
            f"🇺🇸 {amount:,.2f} USD\n\n"
            f"🇰🇷 약 {krw:,.0f} KRW"
        )

    # 엔화
    if "엔" in text or "jpy" in text.lower():
        jpy_krw = rates["KRW"] / rates["JPY"]
        krw = amount * jpy_krw

        return (
            f"🇯🇵 {amount:,.0f} JPY\n\n"
            f"🇰🇷 약 {krw:,.0f} KRW"
        )

    # 유로
    if "유로" in text or "eur" in text.lower():
        eur_krw = rates["KRW"] / rates["EUR"]
        krw = amount * eur_krw

        return (
            f"🇪🇺 {amount:,.2f} EUR\n\n"
            f"🇰🇷 약 {krw:,.0f} KRW"
        )

    # 위안
    if "위안" in text or "cny" in text.lower():
        cny_krw = rates["KRW"] / rates["CNY"]
        krw = amount * cny_krw

        return (
            f"🇨🇳 {amount:,.2f} CNY\n\n"
            f"🇰🇷 약 {krw:,.0f} KRW"
        )

    return None


# =========================================================
# /start
# =========================================================
def start_message():
    return (
        "🤖 환율봇에 오신 것을 환영합니다!\n\n"

        "📌 사용방법\n\n"

        "환율\n"
        "→ 주요 환율 확인\n\n"

        "100달러\n"
        "→ 100 USD를 원화로 환산\n\n"

        "100엔\n"
        "→ 100 JPY를 원화로 환산\n\n"

        "100유로\n"
        "→ 100 EUR를 원화로 환산\n\n"

        "100위안\n"
        "→ 100 CNY를 원화로 환산\n\n"

        "━━━━━━━━━━━━━━\n"
        "💡 예시\n"
        "환율\n"
        "100달러\n"
        "50000엔"
    )


# =========================================================
# Telegram 업데이트 처리
# =========================================================
def process_update(update):

    if "message" not in update:
        return

    message = update["message"]

    if "text" not in message:
        return

    chat_id = message["chat"]["id"]
    text = message["text"].strip()

    print(f"받은 메시지: {text}")

    # /start
    if text.lower() == "/start":
        send_message(
            chat_id,
            start_message()
        )
        return

    # 환율
    if text in ["환율", "/환율", "/exchange", "exchange"]:
        try:
            result = exchange_message()

            send_message(
                chat_id,
                result
            )

        except Exception as e:

            print("환율 조회 오류:", e)

            send_message(
                chat_id,
                "⚠️ 환율 정보를 가져오지 못했습니다.\n잠시 후 다시 시도해주세요."
            )

        return

    # 통화 환산
    result = convert_currency(text)

    if result:

        send_message(
            chat_id,
            result
        )

        return

    # 알 수 없는 명령
    send_message(
        chat_id,
        "🤖 명령을 이해하지 못했습니다.\n\n"
        "사용 예:\n"
        "• 환율\n"
        "• 100달러\n"
        "• 1000엔\n"
        "• 100유로\n"
        "• 100위안"
    )


# =========================================================
# Telegram Long Polling
# =========================================================
def main():

    print("================================")
    print("🤖 환율봇 시작")
    print("================================")

    offset = 0

    while True:

        try:

            response = requests.get(
                f"{TELEGRAM_API}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 30
                },
                timeout=40
            )

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                print("Telegram API 오류:", data)
                time.sleep(5)
                continue

            updates = data.get("result", [])

            for update in updates:

                offset = update["update_id"] + 1

                try:
                    process_update(update)

                except Exception as e:
                    print("업데이트 처리 오류:", e)

        except requests.exceptions.Timeout:

            # Long polling timeout은 정상
            continue

        except Exception as e:

            print("서버 오류:", e)

            time.sleep(5)


# =========================================================
# 실행
# =========================================================
if __name__ == "__main__":
    main()
