import csv
from io import StringIO
from typing import Any, Dict, List


def tasks_to_csv(tasks: List[Dict[str, Any]]) -> str:
    output = StringIO()
    fieldnames = [
        "task",
        "project",
        "deadline",
        "importance",
        "client_value",
        "deadline_score",
        "importance_score",
        "client_value_score",
        "estimated_hours",
        "priority_score",
        "priority_level",
        "reason",
        "next_step",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in tasks:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    return output.getvalue()


def report_to_markdown(result: Dict[str, Any]) -> str:
    tasks = result.get("tasks", [])
    plan = result.get("plan", {})
    recommendations = result.get("recommendations", [])

    lines = [
        "# Отчет: ИИ-менеджер задач для фрилансера",
        "",
        "## 1. Приоритизированные задачи",
        "",
    ]

    if not tasks:
        lines.append("- Нет задач в результате.")
    else:
        for idx, task in enumerate(tasks, start=1):
            lines.extend(
                [
                    f"### {idx}. {task.get('task', 'Без названия')}",
                    f"- Проект: {task.get('project', '-')}",
                    f"- Дедлайн: {task.get('deadline', '-')}",
                    f"- Важность: {task.get('importance', '-')}",
                    f"- Оценка времени: {task.get('estimated_hours', '-')}",
                    f"- Приоритет: {task.get('priority_level', '-')} (score: {task.get('priority_score', '-')})",
                    f"- Почему: {task.get('reason', '-')}",
                    f"- Следующий шаг: {task.get('next_step', '-')}",
                    "",
                ]
            )

    lines.extend(["## 2. План выполнения", ""])
    for key in ("today", "tomorrow", "this_week"):
        lines.append(f"### {key}")
        items = plan.get(key, [])
        if not items:
            lines.append("- Нет задач")
        else:
            lines.extend([f"- {item}" for item in items])
        lines.append("")

    lines.extend(["## 3. Рекомендации", ""])
    if not recommendations:
        lines.append("- Рекомендации не получены.")
    else:
        lines.extend([f"- {item}" for item in recommendations])

    return "\n".join(lines).strip() + "\n"
