# ИИ-менеджер задач для фрилансеров

MVP-проект на `Streamlit + LangChain`, который:
- анализирует список задач фрилансера;
- приоритизирует задачи (срочность + важность + доходность клиента);
- формирует план выполнения;
- экспортирует результат в `.csv` и `.md`.
- синхронизирует план с Google/Яндекс Календарем через `.ics`.

## 1) Стек

- Python 3.10+
- Streamlit
- LangChain
- OpenAI API (через `langchain-openai`)

## 2) Структура проекта

```text
.
├─ app.py
├─ requirements.txt
├─ .env.example
├─ prompts/
│  ├─ system_prompt.md
│  └─ user_prompt.md
├─ report/
│  ├─ commercial_offer.md
│  ├─ commercial_offer_with_screenshots.md
│  └─ screenshots/
└─ src/
   ├─ calendar_sync.py
   ├─ llm_chain.py
   └─ exporters.py
```

## 3) Быстрый запуск

1. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Создать `.env` на основе `.env.example` и добавить ключ:
   ```env
   OPENAI_API_KEY=...
   OPENAI_MODEL=gpt-4o-mini
   ```
3. Запустить приложение:
   ```bash
   streamlit run app.py
   ```

## 4) Как пользоваться

1. Введите задачи (по одной строке).
2. Укажите сроки, важность, доходность клиента, длительность и контекст.
3. Нажмите **Сгенерировать план**.
4. Скачайте:
   - `tasks_plan.csv` (структурированный список),
   - `tasks_report.md` (отчет для сдачи/презентации).
5. При необходимости синхронизируйте план с календарем:
   - нажмите кнопку скачивания `.ics` для Google или Яндекс;
   - импортируйте файл в календарь;
   - уведомления начнут приходить из календаря.

## 5) Синхронизация с календарями

- Доступны два файла экспорта: для Google Calendar и Яндекс Календаря.
- В каждом событии есть описание, приоритет и следующий шаг.
- Добавлены напоминания:
  - за 1 день до дедлайна,
  - за 1 час до дедлайна.

## 6) Формат входных задач

Рекомендуемый формат одной строки:

```text
[Проект] Название задачи | дедлайн: YYYY-MM-DD | важность: 1-5 | доходность: 1-5 | часы: 1-8
```

Пример:

```text
[Сайт клиента А] Подготовить 3 баннера | дедлайн: 2026-05-10 | важность: 4 | доходность: 5 | часы: 3
```

## 7) Формула приоритизации

`priority_score = 0.45 * deadline_score + 0.35 * importance_score + 0.20 * client_value_score`

- `deadline_score` (1..5): чем ближе дедлайн, тем выше балл;
- `importance_score` (1..5): берется из важности задачи;
- `client_value_score` (1..5): доходность/ценность клиента.

Уровни:
- `high`: score >= 4.0
- `medium`: 2.8 <= score < 4.0
- `low`: score < 2.8

## 8) Что показывает система

- Таблица приоритизированных задач;
- План по блокам: `today`, `tomorrow`, `this_week`;
- Рекомендации по организации рабочего процесса.

## 9) Идеи для развития

- Telegram-бот интерфейс;
- подключение Google Calendar;
- сохранение истории планов;
- RAG с личной базой знаний по клиентам.

## 10) Репозиторий на GitHub

Публичный репозиторий: [maxmineew/AI-Task-Manager-](https://github.com/maxmineew/AI-Task-Manager-)

Перед первым `push` убедитесь, что в индекс не попали секреты: файл `.env` уже в `.gitignore`, используйте только `.env.example`.

```bash
git remote add origin https://github.com/maxmineew/AI-Task-Manager-.git
git branch -M main
git add -A
git status
git commit -m "Initial commit: AI Task Manager MVP"
git push -u origin main
```

Если `origin` уже добавлен с другим URL:

```bash
git remote set-url origin https://github.com/maxmineew/AI-Task-Manager-.git
```

На Windows удобно запускать так: `py -m streamlit run app.py` из корня репозитория.
