import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"


def ask_ai(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["response"]


if __name__ == "__main__":
    answer = ask_ai(
        "You are a job-search assistant. "
        "Explain in 3 short sentences what a backend software engineer does."
    )

    print("\nAI RESPONSE:\n")
    print(answer)