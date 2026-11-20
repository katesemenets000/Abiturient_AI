
import csv
import json
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).parent

INPUT_FILE = BASE_DIR / "model_comparison.csv"
DETAILS_FILE = BASE_DIR / "evaluation_details.csv"
SUMMARY_FILE = BASE_DIR / "evaluation_summary.csv"


def load_results():
    with open(INPUT_FILE, encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def evaluate():
    results = load_results()

    details = []
    statistics = defaultdict(list)

    for row in results:
        expected = set(json.loads(row["expected"]))
        predicted = set(json.loads(row["matched_clusters"] or "[]"))

        missing = expected - predicted
        extra = predicted - expected

        exact_match = expected == predicted

        # Метрики для тестов, где ожидаются конкретные кластеры
        if expected:
            precision = len(expected & predicted) / len(predicted) if predicted else 0
            recall = len(expected & predicted) / len(expected)
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall else 0
            )
        else:
            precision = ""
            recall = ""
            f1 = ""

        details.append({
            "model": row["model"],
            "test_id": row["test_id"],
            "type": row["type"],
            "expected": ", ".join(sorted(expected)),
            "predicted": ", ".join(sorted(predicted)),
            "exact_match": exact_match,
            "missing_clusters": ", ".join(sorted(missing)),
            "extra_clusters": ", ".join(sorted(extra)),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "needs_clarification": row["needs_clarification"]
        })

        statistics[row["model"]].append({
            "type": row["type"],
            "exact_match": exact_match,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "missing": len(missing),
            "extra": len(extra)
        })

    # Сохраняем подробные результаты
    with open(DETAILS_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=details[0].keys())
        writer.writeheader()
        writer.writerows(details)

    # Формируем общую сводку
    summary = []

    for model, rows in statistics.items():
        direct = [r for r in rows if r["type"] == "direct"]
        non_empty = [r for r in rows if r["precision"] != ""]

        summary.append({
            "model": model,
            "total_tests": len(rows),
            "exact_matches": sum(r["exact_match"] for r in rows),
            "exact_accuracy_percent": round(
                100 * sum(r["exact_match"] for r in rows) / len(rows), 2
            ),
            "direct_tests": len(direct),
            "direct_exact_accuracy_percent": round(
                100 * sum(r["exact_match"] for r in direct) / len(direct), 2
            ) if direct else 0,
            "average_precision": round(
                sum(r["precision"] for r in non_empty) / len(non_empty), 3
            ) if non_empty else 0,
            "average_recall": round(
                sum(r["recall"] for r in non_empty) / len(non_empty), 3
            ) if non_empty else 0,
            "average_f1": round(
                sum(r["f1"] for r in non_empty) / len(non_empty), 3
            ) if non_empty else 0,
            "missing_clusters": sum(r["missing"] for r in rows),
            "extra_clusters": sum(r["extra"] for r in rows)
        })

    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)

    print("Оценка завершена!")
    print("Подробные результаты:", DETAILS_FILE)
    print("Сводная таблица:", SUMMARY_FILE)

    for row in summary:
        print("\nМодель:", row["model"])
        print("Точное совпадение:", row["exact_matches"], "/", row["total_tests"])
        print("Accuracy:", row["exact_accuracy_percent"], "%")
        print("Precision:", row["average_precision"])
        print("Recall:", row["average_recall"])
        print("F1:", row["average_f1"])


if __name__ == "__main__":
    evaluate()
