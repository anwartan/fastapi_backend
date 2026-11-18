
import requests
import os


def ask_openai(messages):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY belum diatur.")

    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "https://api.openai.com/v1"
    )

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-6.1-terra"
    )

    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": 6000,
        "reasoning_effort": "medium",
    }

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=(15, 180),
        )

        response.raise_for_status()

        result = response.json()

        choices = result.get("choices", [])

        if not choices:
            raise ValueError("AI tidak memberikan respons.")

        message = choices[0].get("message", {})
        reply = message.get("content")

        if not reply:
            raise ValueError(
                "Respons AI kosong atau tidak memiliki teks."
            )

        usage = result.get("usage", {})

        return reply, usage

    except requests.exceptions.Timeout:
        raise RuntimeError("Permintaan AI mengalami timeout.")

    except requests.exceptions.HTTPError as e:
        error_detail = response.text[:2000]
        raise RuntimeError(
            f"OpenAI API Error: {error_detail}"
        ) from e

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Gagal menghubungi OpenAI: {str(e)}"
        ) from e
