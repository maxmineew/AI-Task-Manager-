from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import uuid4


def _escape_ics(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )


def _deadline_to_dt(deadline: str) -> datetime:
    return datetime.strptime(deadline, "%Y-%m-%d").replace(hour=9, minute=0, second=0)


def _event_duration_hours(task: Dict[str, Any]) -> float:
    raw = task.get("estimated_hours", 1)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = 1.0
    return min(max(value, 0.5), 8.0)


def build_ics_calendar(result: Dict[str, Any], calendar_name: str = "AI Task Plan") -> str:
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines: List[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AI Task Manager//ZeroCoder//RU",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_escape_ics(calendar_name)}",
        "METHOD:PUBLISH",
    ]

    tasks = result.get("tasks", [])
    for task in tasks:
        deadline = task.get("deadline")
        if not deadline:
            continue
        try:
            start_dt = _deadline_to_dt(str(deadline))
        except ValueError:
            continue

        duration_hours = _event_duration_hours(task)
        end_dt = start_dt + timedelta(hours=duration_hours)
        uid = f"{uuid4()}@ai-task-manager"
        title = task.get("task", "Задача")
        project = task.get("project", "Без проекта")
        priority = task.get("priority_level", "-")
        reason = task.get("reason", "-")
        next_step = task.get("next_step", "-")
        description = (
            f"Проект: {project}\n"
            f"Приоритет: {priority}\n"
            f"Обоснование: {reason}\n"
            f"Следующий шаг: {next_step}"
        )

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_utc}",
                f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{_escape_ics(str(title))}",
                f"DESCRIPTION:{_escape_ics(description)}",
                "BEGIN:VALARM",
                "TRIGGER:-P1D",
                "ACTION:DISPLAY",
                "DESCRIPTION:Напоминание за день до дедлайна",
                "END:VALARM",
                "BEGIN:VALARM",
                "TRIGGER:-PT1H",
                "ACTION:DISPLAY",
                "DESCRIPTION:Напоминание за 1 час до дедлайна",
                "END:VALARM",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
