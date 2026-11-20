import os
import json
import time
import csv

from pathlib import Path
from dotenv import load_dotenv
from gigachat import GigaChat

from test_cases import TEST_CASES


load_dotenv()

credentials = os.getenv("GIGACHAT_CREDENTIALS")

if not credentials:
    raise ValueError("Не найден ключ GigaChat в файле .env")


CERT_PATH = Path(__file__).with_name("russian_trusted_root_ca_pem.crt")

MODELS = [
    "GigaChat-2",
    "GigaChat-2-Pro",
    "GigaChat-3-Pro"
]

print("Количество тестов:", len(TEST_CASES))
print("Модели для проверки:", MODELS)


CLUSTERS = """
K1 — разработка и информационные технологии.
K2 — анализ данных, искусственный интеллект и математика.
K3 — кибербезопасность.
K4 — инженерия и технические системы.
K5 — бизнес и управление.
K6 — экономика и финансы.
K7 — дизайн и визуальные коммуникации.
K8 — медиа и коммуникации.
K9 — гуманитарные науки.
K10 — общество, право и политика.
K11 — психология, биология и естественные науки.
K12 — городская среда, строительство и сценическое искусство.
"""


PROMPT_TEMPLATE = """
Ты — модуль анализа интересов абитуриента
для системы профориентации.

Твоя задача — определить образовательные кластеры,
которые подтверждаются непосредственно ответом абитуриента.

Список кластеров:
{clusters}

Ответ абитуриента:
"{answer}"

СТРОГИЕ ПРАВИЛА:

1. Выбирай только кластеры, для которых есть
   конкретные подтверждения в ответе.

2. Не придумывай интересы, способности и предпочтения.

3. Если абитуриент говорит, что пока не знает,
   чего хочет, не выбирай кластеры без дополнительных
   подтверждений.

4. Если информации недостаточно, верни пустой список
   matched_clusters и установи needs_clarification: true.

5. Учитывай отрицания. Например, если абитуриент
   не любит программирование, это не является основанием
   выбирать кластер разработки и ИТ.

6. Различай близкие направления:
   - К5 — бизнес и управление;
   - К6 — экономика и финансы;
   - К10 — общество, право и политика.

7. Не пропускай явно названные интересы.
   Если человек упоминает экономику, обязательно
   рассмотри К6.

8. Не выбирай кластер только потому, что он кажется
   логичным дополнением к другому кластеру.

9. Если интересов несколько, можно выбрать несколько
   подтверждённых кластеров.

Верни только JSON, без пояснений до и после него.

ВАЖНО:
Поле matched_clusters всегда должно быть массивом
строк с кодами кластеров.

Правильный формат:
"matched_clusters": ["K1", "K2"]

Запрещено помещать внутрь массива объекты.
Не добавляй confidence для отдельных кластеров.
Общая уверенность указывается только в поле confidence.

Формат:
{{
    "matched_clusters": [],
    "confidence": 0.0,
    "needs_clarification": true,
    "reason": "Объяснение решения"
}}

Поле reason обязательно должно содержать краткое
объяснение выбора кластеров.

Не оставляй reason пустым даже в том случае,
если выбрано несколько кластеров.

Если matched_clusters пустой, объясни,
почему информации недостаточно.

confidence — оценка уверенности от 0 до 1.
"""


def analyze_answer(giga, answer):
    prompt = PROMPT_TEMPLATE.format(
        clusters=CLUSTERS,
        answer=answer
    )

    response = giga.chat.create(prompt)

    return response.messages[0].content[0].text


    
def parse_model_response(raw_text):
    """Преобразует ответ модели из текста в JSON."""
    text = raw_text.strip()

    # Убираем возможные маркеры Markdown
    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "").strip()

    # Если модель добавила текст вокруг JSON,
    # пытаемся выделить сам JSON-объект
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("В ответе не найден JSON")

    return json.loads(text[start:end + 1])


def run_tests():
    results = []

    fieldnames = [
        "model",
        "test_id",
        "type",
        "answer",
        "expected",
        "matched_clusters",
        "confidence",
        "needs_clarification",
        "reason",
        "valid_json",
        "error",
        "raw_response",
        "elapsed_seconds"
    ]

    output_path = Path(__file__).with_name("model_comparison.csv")

    for model in MODELS:
        print("\n" + "=" * 60)
        print("ТЕСТИРУЕМ МОДЕЛЬ:", model)
        print("=" * 60)

        try:
            with GigaChat(
                credentials=credentials,
                ca_bundle_file=str(CERT_PATH),
                model=model
            ) as giga:

                for case in TEST_CASES:
                    print(f"Тест {case['id']}/34...", end=" ")

                    start_time = time.perf_counter()

                    row = {
                        "model": model,
                        "test_id": case["id"],
                        "type": case["type"],
                        "answer": case["answer"],
                        "expected": json.dumps(
                            case["expected"], ensure_ascii=False
                        ),
                        "matched_clusters": "",
                        "confidence": "",
                        "needs_clarification": "",
                        "reason": "",
                        "valid_json": False,
                        "error": "",
                        "raw_response": "",
                        "elapsed_seconds": ""
                    }

                    try:
                        raw_text = analyze_answer(
                            giga,
                            case["answer"]
                        )

                        row["raw_response"] = raw_text

                        data = parse_model_response(raw_text)

                        row["matched_clusters"] = json.dumps(
                            data.get("matched_clusters", []),
                            ensure_ascii=False
                        )
                        row["confidence"] = data.get("confidence", "")
                        row["needs_clarification"] = data.get(
                            "needs_clarification", ""
                        )
                        row["reason"] = data.get("reason", "")
                        row["valid_json"] = True

                        print("JSON получен")

                    except Exception as error:
                        row["error"] = str(error)
                        print("ОШИБКА:", error)

                    row["elapsed_seconds"] = round(
                        time.perf_counter() - start_time, 2
                    )

                    results.append(row)

                    # Сохраняем результаты после каждого теста
                    with open(
                        output_path,
                        "w",
                        newline="",
                        encoding="utf-8-sig"
                    ) as file:
                        writer = csv.DictWriter(
                            file,
                            fieldnames=fieldnames
                        )
                        writer.writeheader()
                        writer.writerows(results)

        except Exception as error:
            print("Ошибка при работе с моделью:", error)

    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("Всего обработано ответов:", len(results))
    print("Файл с результатами:", output_path)


if __name__ == "__main__":
    run_tests()
