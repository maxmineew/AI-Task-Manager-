import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"


def _read_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("LLM вернула невалидный JSON.")
        return json.loads(text[start : end + 1])


def _validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_keys = {"tasks", "plan", "recommendations"}
    if not required_keys.issubset(payload.keys()):
        missing = required_keys.difference(payload.keys())
        raise ValueError(f"В ответе LLM не хватает ключей: {', '.join(sorted(missing))}")
    return payload


def build_plan_with_langchain(
    tasks_input: str,
    extra_context: str,
    hours_today: int,
    hours_tomorrow: int,
) -> Dict[str, Any]:
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise ValueError("Не найден OPENAI_API_KEY в .env")

    system_prompt = _read_prompt("system_prompt.md")
    user_prompt_template = _read_prompt("user_prompt.md")
    user_prompt = user_prompt_template.format(
        tasks_input=tasks_input.strip(),
        extra_context=extra_context.strip() or "Нет дополнительного контекста",
        hours_today=hours_today,
        hours_tomorrow=hours_tomorrow,
    )

    llm = ChatOpenAI(model=model_name, temperature=0.2, api_key=api_key)
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    payload = _extract_json(response.content)
    return _validate_payload(payload)
