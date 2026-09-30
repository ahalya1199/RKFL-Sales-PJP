import os
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "rkfl-whatsapp-test")


@app.get("/")
def health():
    return "RKFL Sales PJP bot is running"


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Forbidden", 403


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured in Render")

    if not base_url:
        raise RuntimeError("OPENAI_BASE_URL is not configured in Render")

    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )


def interpret_message(message_text):
    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-5-nano-2025-08-07",
        messages=[
            {
                "role": "system",
                "content": """
You are the RKFL Sales PJP assistant.

Your job is to interpret messages from salespeople about
their sales plans and customer visits.

For now, do NOT make any updates.

Return JSON with exactly these fields:

{
  "action": "plan_visit | record_visit | query | other",
  "date": null,
  "city": null,
  "customer": null,
  "details": null
}

Rules:
- Only extract information explicitly stated or strongly implied.
- Do not invent customer names, cities or dates.
- If information is missing, use null.
- Return JSON only.
"""
            },
            {
                "role": "user",
                "content": message_text
            }
        ]
    )

    return response.choices[0].message.content


@app.post("/webhook")
def receive_webhook():
    data = request.get_json(silent=True) or {}

    try:
        entry = data.get("entry", [])

        for entry_item in entry:
            for change in entry_item.get("changes", []):
                value = change.get("value", {})

                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                name = "Unknown"

                if contacts:
                    name = contacts[0].get(
                        "profile", {}
                    ).get("name", "Unknown")

                for message in messages:
                    sender = message.get("from", "Unknown")
                    message_type = message.get("type")

                    if message_type == "text":
                        text = message.get("text", {}).get("body", "")

                        print("----- WHATSAPP MESSAGE -----", flush=True)
                        print(f"Name: {name}", flush=True)
                        print(f"From: {sender}", flush=True)
                        print(f"Message: {text}", flush=True)

                        try:
                            interpretation = interpret_message(text)

                            print(
                                "----- OPENAI INTERPRETATION -----",
                                flush=True
                            )
                            print(interpretation, flush=True)
                            print(
                                "---------------------------------",
                                flush=True
                            )

                        except Exception as ai_error:
                            print(
                                f"OpenAI error: {ai_error}",
                                flush=True
                            )

                        print("----------------------------", flush=True)

                    else:
                        print(
                            "----- WHATSAPP EVENT -----",
                            flush=True
                        )
                        print(f"Name: {name}", flush=True)
                        print(f"From: {sender}", flush=True)
                        print(
                            f"Message type: {message_type}",
                            flush=True
                        )
                        print("---------------------------", flush=True)

    except Exception as e:
        print(f"Webhook error: {e}", flush=True)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
