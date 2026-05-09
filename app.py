import json

import streamlit as st

from src.calendar_sync import build_ics_calendar
from src.exporters import report_to_markdown, tasks_to_csv
from src.llm_chain import build_plan_with_langchain


def estimate_business_value(tasks: list[dict], hours_today: int, hours_tomorrow: int) -> dict:
    task_count = len(tasks)
    high_priority_count = sum(1 for t in tasks if t.get("priority_level") == "high")
    estimated_hours = 0.0
    for task in tasks:
        try:
            estimated_hours += float(task.get("estimated_hours", 0))
        except (TypeError, ValueError):
            continue

    planning_time_saved_min = min(90, 15 + task_count * 6)
    execution_focus_growth_pct = min(45, 10 + high_priority_count * 4)
    overload_risk_drop_pct = min(60, 12 + max(0, estimated_hours - (hours_today + hours_tomorrow)) * 4)

    return {
        "planning_time_saved_min": int(planning_time_saved_min),
        "execution_focus_growth_pct": int(execution_focus_growth_pct),
        "overload_risk_drop_pct": int(overload_risk_drop_pct),
        "high_priority_count": high_priority_count,
    }


def build_commercial_offer_md(result: dict, value: dict) -> str:
    tasks = result.get("tasks", [])
    top_tasks = tasks[:3]
    lines = [
        "# Коммерческое предложение",
        "",
        "## AI Task Manager для фрилансеров и агентств",
        "",
        "### Бизнес-результат",
        f"- Экономия времени на планировании: до {value['planning_time_saved_min']} мин/день",
        f"- Рост фокуса на приоритетных задачах: до +{value['execution_focus_growth_pct']}%",
        f"- Снижение риска перегруза: до -{value['overload_risk_drop_pct']}%",
        "",
        "### Что получает клиент",
        "- Автоматическую приоритизацию задач по дедлайнам, важности и доходности.",
        "- Готовый план работы: today / tomorrow / this_week.",
        "- Экспорт отчетов в CSV/Markdown и синхронизацию с календарем (.ics).",
        "",
        "### Топ-задачи из демонстрации",
    ]
    if top_tasks:
        for item in top_tasks:
            lines.append(
                f"- {item.get('task', 'Задача')} (priority: {item.get('priority_level', '-')}, score: {item.get('priority_score', '-')})"
            )
    else:
        lines.append("- Будут сформированы после запуска анализа.")

    lines.extend(
        [
            "",
            "### Пакеты внедрения",
            "- Start: MVP за 5-7 дней.",
            "- Pro: интеграция в процессы команды + кастомные правила.",
            "- Team: роли, сценарии по клиентам, поддержка и развитие.",
            "",
            "### Следующий шаг",
            "Провести 20-минутный разбор ваших рабочих задач и запустить пилот на реальных данных.",
            "",
        ]
    )
    return "\n".join(lines)


st.set_page_config(page_title="ИИ-менеджер задач", page_icon="🧠", layout="wide")
st.title("🧠 AI Task Manager для фрилансеров и агентств")
st.caption("Коммерческая версия: планирование, приоритизация, календарь, отчеты")

st.markdown(
    """
**Продающее позиционирование продукта**  
AI Task Manager снижает хаос в задачах, помогает не срывать дедлайны и фокусирует на задачах,
которые дают деньги и удерживают клиентов.
"""
)

with st.sidebar:
    st.header("Настройки")
    hours_today = st.slider("Часов на сегодня", min_value=1, max_value=12, value=6)
    hours_tomorrow = st.slider("Часов на завтра", min_value=1, max_value=12, value=6)

st.subheader("Входные данные")
demo_tasks = (
    "[Клиент Alfa] Финализировать лендинг | дедлайн: 2026-05-08 | важность: 5 | доходность: 5 | часы: 3\n"
    "[Клиент Beta] Подготовить медиаплан | дедлайн: 2026-05-10 | важность: 4 | доходность: 4 | часы: 2\n"
    "[Личный бренд] Написать экспертный пост | дедлайн: 2026-05-12 | важность: 3 | доходность: 2 | часы: 1.5\n"
    "[Клиент Gamma] Созвон по новому ТЗ | дедлайн: 2026-05-09 | важность: 4 | доходность: 5 | часы: 1\n"
    "[Операционка] Разобрать входящие письма | дедлайн: 2026-05-11 | важность: 2 | доходность: 1 | часы: 1"
)
demo_context = (
    "Приоритет: сохранить дедлайны по клиентам Alfa и Gamma. "
    "Просрочка по Alfa может повлиять на продление контракта. "
    "Оптимальный фокус для глубоких задач: 10:00-14:00."
)

if "tasks_input_value" not in st.session_state:
    st.session_state["tasks_input_value"] = ""
if "extra_context_value" not in st.session_state:
    st.session_state["extra_context_value"] = ""
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "offer_md_content" not in st.session_state:
    st.session_state["offer_md_content"] = ""

if st.button("Загрузить демо-набор задач", use_container_width=True):
    st.session_state["tasks_input_value"] = demo_tasks
    st.session_state["extra_context_value"] = demo_context
    st.success("Демо-набор загружен. Нажмите «Сгенерировать план».")

tasks_input = st.text_area(
    "Список задач (по одной строке):",
    key="tasks_input_value",
    height=220,
    placeholder=(
        "[Клиент А] Подготовить баннеры | дедлайн: 2026-05-10 | важность: 4 | доходность: 5 | часы: 3\n"
        "[Личный бренд] Написать пост в Telegram | дедлайн: 2026-05-09 | важность: 3 | доходность: 2 | часы: 1.5\n"
        "[Клиент Б] Созвон по ТЗ | дедлайн: 2026-05-08 | важность: 5 | доходность: 4 | часы: 1"
    ),
)
extra_context = st.text_area(
    "Дополнительный контекст (необязательно):",
    key="extra_context_value",
    height=120,
    placeholder="Например: самые важные клиенты, штрафы за просрочку, пик продуктивности по времени.",
)

generate_btn = st.button("Сгенерировать план", type="primary", use_container_width=True)

if generate_btn:
    if not tasks_input.strip():
        st.warning("Добавьте хотя бы одну задачу.")
        st.stop()

    with st.spinner("LLM анализирует задачи и формирует план..."):
        try:
            result = build_plan_with_langchain(
                tasks_input=tasks_input,
                extra_context=extra_context,
                hours_today=hours_today,
                hours_tomorrow=hours_tomorrow,
            )
        except Exception as exc:
            st.error(f"Ошибка при генерации: {exc}")
            st.stop()

    st.session_state["last_result"] = result

result = st.session_state["last_result"]
if result:
    tasks = result.get("tasks", [])
    plan = result.get("plan", {})
    recommendations = result.get("recommendations", [])
    value = estimate_business_value(tasks, hours_today, hours_tomorrow)

    st.success("План успешно сформирован.")

    st.subheader("Ценность для клиента")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Экономия на планировании", f"{value['planning_time_saved_min']} мин/день")
    m2.metric("Рост фокуса на важном", f"+{value['execution_focus_growth_pct']}%")
    m3.metric("Снижение риска перегруза", f"-{value['overload_risk_drop_pct']}%")
    m4.metric("High-priority задач", value["high_priority_count"])

    st.subheader("Приоритизированные задачи")
    if tasks:
        st.dataframe(tasks, use_container_width=True)
    else:
        st.info("Модель не вернула список задач.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Today")
        for item in plan.get("today", []):
            st.write(f"- {item}")
    with col2:
        st.markdown("### Tomorrow")
        for item in plan.get("tomorrow", []):
            st.write(f"- {item}")
    with col3:
        st.markdown("### This Week")
        for item in plan.get("this_week", []):
            st.write(f"- {item}")

    st.subheader("Рекомендации")
    if recommendations:
        for rec in recommendations:
            st.write(f"- {rec}")
    else:
        st.info("Рекомендации не получены.")

    st.subheader("Коммерческие пакеты внедрения")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("**Start**")
        st.markdown("- MVP за 5-7 дней")
        st.markdown("- Базовая приоритизация")
        st.markdown("- Экспорт CSV/MD/ICS")
    with p2:
        st.markdown("**Pro**")
        st.markdown("- Все из Start")
        st.markdown("- Интеграция в процессы команды")
        st.markdown("- Кастомные правила приоритизации")
    with p3:
        st.markdown("**Team**")
        st.markdown("- Все из Pro")
        st.markdown("- Роли и сценарии по клиентам")
        st.markdown("- Поддержка и развитие")

    with st.expander("Raw JSON результата"):
        st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")

    csv_content = tasks_to_csv(tasks)
    md_content = report_to_markdown(result)
    calendar_ics = build_ics_calendar(result, calendar_name="AI Tasks")

    with st.sidebar:
        st.divider()
        st.subheader("Экспорт")
        st.download_button(
            label="Скачать CSV",
            data=csv_content,
            file_name="tasks_plan.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            label="Скачать MD отчет",
            data=md_content,
            file_name="tasks_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

        st.subheader("Синхронизация с календарем")
        st.download_button(
            label="Cкачать .ics для Календаря",
            data=calendar_ics,
            file_name="calendar_tasks.ics",
            mime="text/calendar",
            use_container_width=True,
        )

        st.subheader("КП для клиента")
        if st.button("Сформировать КП для клиента", use_container_width=True):
            st.session_state["offer_md_content"] = build_commercial_offer_md(result, value)
            st.success("КП сформировано.")

        if st.session_state.get("offer_md_content"):
            st.download_button(
                label="Скачать КП (.md)",
                data=st.session_state["offer_md_content"],
                file_name="commercial_offer_auto.md",
                mime="text/markdown",
                use_container_width=True,
            )
