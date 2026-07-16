from __future__ import annotations

import math
from typing import Any


class Statistics:
    @staticmethod
    def confusion_matrix(
        predicted: list[Any],
        actual: list[Any],
        labels: list[Any],
    ) -> dict[str, Any]:
        n = len(labels)
        matrix = [[0] * n for _ in range(n)]
        label_to_idx = {l: i for i, l in enumerate(labels)}
        for p, a in zip(predicted, actual):
            pi = label_to_idx.get(p, -1)
            ai = label_to_idx.get(a, -1)
            if pi >= 0 and ai >= 0:
                matrix[ai][pi] += 1
        return {
            "labels": labels,
            "matrix": matrix,
            "accuracy": Statistics.accuracy(predicted, actual),
        }

    @staticmethod
    def accuracy(predicted: list[Any], actual: list[Any]) -> float:
        if not predicted or not actual:
            return 0.0
        correct = sum(1 for p, a in zip(predicted, actual) if p == a)
        return correct / len(predicted)

    @staticmethod
    def precision_score(
        predicted: list[Any], actual: list[Any], pos_label: Any = None,
    ) -> float:
        if pos_label is not None:
            tp = sum(1 for p, a in zip(predicted, actual) if p == pos_label and a == pos_label)
            fp = sum(1 for p, a in zip(predicted, actual) if p == pos_label and a != pos_label)
            return tp / (tp + fp) if (tp + fp) > 0 else 0.0
        labels = set(actual)
        scores = []
        for lbl in labels:
            tp = sum(1 for p, a in zip(predicted, actual) if p == lbl and a == lbl)
            fp = sum(1 for p, a in zip(predicted, actual) if p == lbl and a != lbl)
            if tp + fp > 0:
                scores.append(tp / (tp + fp))
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def recall_score(
        predicted: list[Any], actual: list[Any], pos_label: Any = None,
    ) -> float:
        if pos_label is not None:
            tp = sum(1 for p, a in zip(predicted, actual) if p == pos_label and a == pos_label)
            fn = sum(1 for p, a in zip(predicted, actual) if p != pos_label and a == pos_label)
            return tp / (tp + fn) if (tp + fn) > 0 else 0.0
        labels = set(actual)
        scores = []
        for lbl in labels:
            tp = sum(1 for p, a in zip(predicted, actual) if p == lbl and a == lbl)
            fn = sum(1 for p, a in zip(predicted, actual) if p != lbl and a == lbl)
            if tp + fn > 0:
                scores.append(tp / (tp + fn))
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def f1_score(
        predicted: list[Any], actual: list[Any], pos_label: Any = None,
    ) -> float:
        p = Statistics.precision_score(predicted, actual, pos_label)
        r = Statistics.recall_score(predicted, actual, pos_label)
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    @staticmethod
    def mcnemar_test(
        correct_a: int, incorrect_a: int,
        correct_b: int, incorrect_b: int,
    ) -> dict[str, float]:
        b = incorrect_a
        c = incorrect_b
        numerator = (abs(b - c) - 1) ** 2
        denominator = b + c
        if denominator == 0:
            chi2 = 0.0
        else:
            chi2 = numerator / denominator
        return {
            "chi_square": chi2,
            "significant": chi2 > 3.841,
            "p_value_approx": "p < 0.05" if chi2 > 3.841 else "p >= 0.05",
        }

    @staticmethod
    def confidence_interval(
        values: list[float], confidence: float = 0.95,
    ) -> dict[str, float]:
        n = len(values)
        if n < 2:
            return {"mean": Statistics.mean(values), "lower": 0, "upper": 0}
        mean_v = Statistics.mean(values)
        se = Statistics.std_dev(values) / math.sqrt(n)
        z = 1.96 if confidence >= 0.95 else 1.645
        return {
            "mean": mean_v,
            "lower": mean_v - z * se,
            "upper": mean_v + z * se,
            "std_error": se,
            "confidence": confidence,
        }

    @staticmethod
    def mean(values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def std_dev(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean_v = Statistics.mean(values)
        variance = sum((x - mean_v) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
