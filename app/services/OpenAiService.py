
import os
import requests
from typing import Any

from fastapi import HTTPException


def ask_openai(
    messages: list[dict[str, str]]
) -> tuple[str, dict[str, Any] | None]:

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "https://api.openai.com/v1"
    ).strip().rstrip("/")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY belum dikonfigurasi."
        )

    if not model:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_MODEL belum dikonfigurasi."
        )

    endpoint = f"{base_url}/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": 6000,
        "n": 1,
    }

    print("[OPENAI] Endpoint:", endpoint)
    print("[OPENAI] Model:", model)
    print("[OPENAI] Jumlah pesan:", len(messages))

    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=(15, 180),
        )

    except requests.Timeout as exc:
        print("[OPENAI TIMEOUT]", repr(exc))

        raise HTTPException(
            status_code=504,
            detail="OpenAI terlalu lama merespons."
        ) from exc

    except requests.RequestException as exc:
        print("[OPENAI CONNECTION ERROR]", repr(exc))

        raise HTTPException(
            status_code=502,
            detail="Tidak dapat menghubungi OpenAI API."
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        print("[OPENAI INVALID JSON]", response.text[:2000])

        raise HTTPException(
            status_code=502,
            detail="Respons OpenAI bukan JSON yang valid."
        ) from exc

    if response.status_code >= 400:

        error_data = (
            data.get("error", {})
            if isinstance(data, dict)
            else {}
        )

        error_message = (
            error_data.get("message", "Unknown error")
            if isinstance(error_data, dict)
            else str(error_data)
        )

        error_type = (
            error_data.get("type")
            if isinstance(error_data, dict)
            else None
        )

        print("[OPENAI ERROR] HTTP:", response.status_code)
        print("[OPENAI ERROR] Type:", error_type)
        print("[OPENAI ERROR] Message:", error_message)

        raise HTTPException(
            status_code=502,
            detail=f"OpenAI HTTP {response.status_code}: {error_message}"
        )

    try:
        choice = data["choices"][0]
        message = choice.get("message", {})
        content = message.get("content") or ""

        finish_reason = choice.get("finish_reason")

        print("[OPENAI] Finish reason:", finish_reason)
        print("[OPENAI] Usage:", data.get("usage"))
        print("[OPENAI] Panjang jawaban:", len(content))

    except (KeyError, IndexError, TypeError) as exc:
        print("[OPENAI FORMAT ERROR]", str(data)[:2000])

        raise HTTPException(
            status_code=502,
            detail="Format jawaban OpenAI tidak dikenali."
        ) from exc

    answer = str(content).strip()

    if not answer:
        print("[OPENAI EMPTY]", str(data)[:2000])

        raise HTTPException(
            status_code=502,
            detail="OpenAI mengirim jawaban kosong."
        )

    usage = data.get("usage")

    return (
        answer,
        usage if isinstance(usage, dict) else None
    )
