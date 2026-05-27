"""Shared LLM proxy helper for all agents"""
import urllib.request, json

PROXY_URL = "http://localhost:6446/v1/chat/completions"
PROXY_KEY = "oc-c30e473254b096df7e8654d27d9829b0103994ea"
MODEL = "deepseek-v4-flash-free"

def generate(prompt: str) -> str:
    """Send prompt to free proxy, return response text"""
    data = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(PROXY_URL, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_KEY}"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]
