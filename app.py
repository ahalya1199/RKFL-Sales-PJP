import os
from flask import Flask, request

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


@app.post("/webhook")
def receive_webhook():
    data = request.get_json(silent=True) or {}

    try:
        # Meta sends WhatsApp events inside entry -> changes -> value
        entry = data.get("entry", [])

        for entry_item in entry:
            for change in entry_item.get("changes", []):
                value = change.get("value", {})

                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                # Name supplied by WhatsApp, when available
                name = "Unknown"
                if contacts:
                    name = contacts[0].get("profile", {}).get("name", "Unknown")

                for message in messages:
                    sender = message.get("from", "Unknown")
                    message_type = message.get("type")

                    # We only process text messages for now
                    if message_type == "text":
                        text = message.get("text", {}).get("body", "")

                        print("----- WHATSAPP MESSAGE -----", flush=True)
                        print(f"Name: {name}", flush=True)
                        print(f"From: {sender}", flush=True)
                        print(f"Message: {text}", flush=True)
                        print("----------------------------", flush=True)

                    else:
                        print("----- WHATSAPP EVENT -----", flush=True)
                        print(f"Name: {name}", flush=True)
                        print(f"From: {sender}", flush=True)
                        print(f"Message type: {message_type}", flush=True)
                        print("---------------------------", flush=True)

    except Exception as e:
        print(f"Error processing webhook: {e}", flush=True)

    # Always acknowledge the webhook quickly
    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
