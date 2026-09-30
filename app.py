import os
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "rkfl-whatsapp-test")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


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


def interpret_message(message_text):
    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions="""
You are the RKFL Sales PJP assistant.

Your job is to interpret messages from salespeople about their
sales plans and customer visits.

For now, do NOT make assumptions and do NOT perform any updates.
Return JSON with these fields:

action:
- plan_visit
- record_visit
- query
- other

date:
- the date mentioned by the salesperson, or null

city:
- city/location mentioned, or null

customer:
- customer/dealer/company mentioned, or null

details:
- any other useful details from the message, or null

Only extract information explicitly stated or strongly implied by
the message. Do not invent customer names, cities or dates.
""",
        input=message_text
    )

    return response.output_text


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
                    name = contacts[0].get("profile", {}).get("name", "Unknown")

                for message in messages:
                    sender = message.get("from", "Unknown")
                    message_type = message.get("type")

                    if message_type == "text":
                        text = message.get("text", {}).get("body", "")

                        print("----- WHATSAPP MESSAGE -----", flush=True)
                        print(f"Name: {name}", flush=True)
                        print(f"From: {sender}", flush=True)
                        print(f"Message: {text}", flush=True)

                        if OPENAI_API_KEY:
                            interpretation = interpret_message(text)

                            print("----- OPENAI INTERPRETATION -----", flush=True)
                            print(interpretation, flush=True)
                            print("---------------------------------", flush=True)
                        else:
                            print("OPENAI_API_KEY is not configured", flush=True)

                        print("----------------------------", flush=True)

                    else:
                        print("----- WHATSAPP EVENT -----", flush=True)
                        print(f"Name: {name}", flush=True)
                        print(f"From: {sender}", flush=True)
                        print(f"Message type: {message_type}", flush=True)
                        print("---------------------------", flush=True)

    except Exception as e:
        print(f"Error processing webhook: {e}", flush=True)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
