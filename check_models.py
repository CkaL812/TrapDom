import requests
import os

# Встав свій ключ сюди або задай через змінну середовища
API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

def check_available_models():
    print("Отримуємо список моделей з OpenRouter...\n")

    res = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=15,
    )

    if res.status_code != 200:
        print(f"❌ Помилка: {res.status_code}")
        print(res.text[:500])
        return

    models = res.json().get("data", [])
    print(f"Всього моделей: {len(models)}\n")

    # Безкоштовні моделі
    free_models = [m for m in models if ":free" in m.get("id", "")]
    print(f"{'='*60}")
    print(f"БЕЗКОШТОВНІ МОДЕЛІ ({len(free_models)}):")
    print(f"{'='*60}")
    for m in free_models:
        print(f"  {m['id']}")

    print()

    # Тест конкретних моделей
    test_models = [
        "google/gemini-flash-1.5:free",
        "google/gemini-flash-1.5-8b:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free",
    ]

    print(f"{'='*60}")
    print("ТЕСТ КОНКРЕТНИХ МОДЕЛЕЙ:")
    print(f"{'='*60}")
    model_ids = {m["id"] for m in models}
    for model_id in test_models:
        status = "✅ доступна" if model_id in model_ids else "❌ недоступна"
        print(f"  {status} — {model_id}")

    print()

    # Живий тест — відправляємо реальний запит
    print(f"{'='*60}")
    print("ЖИВИЙ ТЕСТ (реальний запит):")
    print(f"{'='*60}")
    for model_id in test_models:
        if model_id not in model_ids:
            continue
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Say: OK"}],
                    "max_tokens": 10,
                },
                timeout=15,
            )
            if r.status_code == 200:
                reply = r.json()["choices"][0]["message"]["content"].strip()
                print(f"  ✅ {model_id} → '{reply}'")
            else:
                print(f"  ❌ {model_id} → status={r.status_code} | {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ {model_id} → виняток: {e}")


if __name__ == "__main__":
    check_available_models()