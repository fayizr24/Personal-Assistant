from flask import Flask, request, jsonify
import os
import secrets
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
# from langchain.agents.structured_output import ToolStrategy
from tools import send_email

app = Flask(__name__)

# Your own secret -- set this in Render's environment variables, not in code
MY_SECRET_KEY = os.environ.get("MY_SECRET_KEY")

# Rate limiter setup -- limits requests per IP address
limiter = Limiter(app=app, key_func=get_remote_address)

# LLM + agent setup
llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
 
tools = [send_email]
 
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
You are a helpful voice assistant. You receive commands transcribed from
spoken audio, and your replies will be converted back to speech, so:
- Keep replies short and conversational (1-2 sentences).
- Never use markdown, asterisks, or special formatting -- plain spoken text only.
 
You have access to a send_email tool. Use it whenever the user asks you to
send, email, or write a message to someone. If they don't specify a subject
or recipient, use reasonable defaults based on what they said.
 
After using a tool, briefly confirm what you did in plain spoken language,
e.g. "Okay, I've sent that email." Do not describe the tool call itself.
"""
)


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

    response = agent.invoke({"messages": [{"role": "user", "content": user_text}]})
 
    # Grab the final message from the agent's conversation as the spoken reply
    final_message = response["messages"][-1]
    reply_text = (
        final_message.content
        if isinstance(final_message.content, str)
        else str(final_message.content)
    )
 
    return jsonify({"reply": reply_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)