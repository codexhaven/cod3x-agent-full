#!/usr/bin/env python3
"""Cod3x Agent Runner — same model as Hermes"""
import asyncio, json
import urllib.request, urllib.error

# Read key from Hermes .env
API_KEY = ""
with open("/data/data/com.termux/files/home/.hermes/.env") as f:
    for line in f:
        if line.startswith("GOOGLE_API_KEY="):
            API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

# Same model Hermes uses for chat + generation
MODEL = "gemini-3.1-flash-lite-preview"

def chat(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"API Error ({e.code}): {body[:300]}"

async def main():
    print(f"Model: {MODEL}")
    print("🚀 Cod3x Agent Ready\n")
    history = "You are Cod3x, a multi-agent AI assistant. Be helpful and concise.\n\n"
    while True:
        try:
            user = input("You: ").strip()
            if not user or user in ('/quit', '/exit'):
                break
            prompt = history + f"User: {user}\nCod3x:"
            response = chat(prompt)
            history += f"User: {user}\nCod3x: {response}\n"
            print(f"\nCod3x: {response}\n")
        except KeyboardInterrupt:
            break
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
