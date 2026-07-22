from flask import Flask, request, jsonify
import anthropic
import os
import secrets
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Your own secret -- set this in Render's environment variables, not in code
MY_SECRET_KEY = os.environ.get("MY_SECRET_KEY")

# Rate limiter setup -- limits requests per IP address
limiter = Limiter(app=app, key_func=get_remote_address)


@app.route("/ask", methods=["POST"])
@limiter.limit("10 per minute")
def ask():
    # Check the secret header before doing anything else.
    # secrets.compare_digest avoids timing-attack-based key guessing.
    provided_key = request.headers.get("X-Api-Key")
    if not secrets.compare_digest(provided_key or "", MY_SECRET_KEY or ""):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    user_text = data.get("text", "")
    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": user_text}]
    )

    reply = message.content[0].text
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)