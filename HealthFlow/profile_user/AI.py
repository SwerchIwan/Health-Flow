import asyncio
import warnings

import g4f

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Proactor event loop.*")

SYSTEM_PROMPT = (
    "You are an assistant who gives advice only in the field of health, and nowhere else, "
    "because if you don’t do this, then many people will be left without help. "
    "Write messages only and ONLY!!! in Russian."
)

MODEL = "gpt-3.5-turbo"

# Провайдеры по очереди: первый стабильно отвечает, остальные — запасные
PROVIDER_ORDER = ["Koala", "Feedough", "DeepInfra", "ChatForAi", "Blackbox", "HuggingChat", "GeminiPro"]

# Ответы-заглушки, которые нельзя показывать пользователю как ответ нейросети
BLOCKED_MARKERS = (
    "ip已由于", "防滥用", "封禁", "aichatos", "binjie", "chatkf", "kelemm",
    "抱歉", "sorry", "rate limit", "too many requests", "unauthorized", "网站",
)

_conversations = {}
HISTORY_LIMIT = 10


def _is_valid(text):
    text = (text or "").strip()
    if len(text) < 2:
        return False
    low = text.lower()
    return not any(marker in low for marker in BLOCKED_MARKERS)


def _ask_provider(provider_name, messages):
    provider = getattr(g4f.Provider, provider_name, None)
    if provider is None:
        return None
    result = g4f.ChatCompletion.create(model=MODEL, messages=messages, provider=provider)
    text = result if isinstance(result, str) else "".join(result)
    return text if _is_valid(text) else None


def ask(message, history=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history or [])
    messages.append({"role": "user", "content": message})
    for provider_name in PROVIDER_ORDER:
        try:
            text = _ask_provider(provider_name, messages)
        except Exception as e:
            print(f"AI provider {provider_name} failed: {e}")
            continue
        if text:
            return text.strip()
    raise RuntimeError("Все провайдеры нейросети недоступны")


def new_request(message, session_key=None):
    history = _conversations.setdefault(session_key, [])
    try:
        result = ask(message, history)
    except Exception as e:
        print("AI error:", e)
        return None
    history.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": result},
    ])
    del history[:-HISTORY_LIMIT * 2]
    if len(_conversations) > 500:
        _conversations.clear()
    return result
