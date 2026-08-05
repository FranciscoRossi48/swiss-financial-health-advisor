import pandas as pd

from swiss_financial_health.clustering import fit_user_segments, label_segment


def _users():
    rows = []
    for i in range(6):
        rows.append(
            {
                "user_id": f"U{i}",
                "avg_income": 5000.0 + i * 100,
                "avg_savings_rate": 0.05 if i < 3 else 0.20,
                "avg_debt_to_income": 0.05,
                "avg_discretionary_ratio": 0.10,
                "income_cv": 0.10,
                "financial_health_score": 60.0,
            }
        )
    return pd.DataFrame(rows)


def test_fit_user_segments_assigns_every_user_to_a_cluster():
    segmented, centroids, silhouette = fit_user_segments(_users(), n_clusters=2)
    assert segmented["segment"].notna().all()
    assert len(centroids) == 2
    assert -1 <= silhouette <= 1


def test_fit_user_segments_produces_segment_labels_for_every_user():
    segmented, _, _ = fit_user_segments(_users(), n_clusters=2)
    assert segmented["segment_label"].notna().all()
    assert set(segmented["segment_label"]).issubset(
        {"Debt pressure", "Variable income", "Stable saver", "High discretionary", "Balanced user"}
    )


def test_label_segment_prioritizes_debt_pressure_over_other_signals():
    row = pd.Series(
        {
            "avg_debt_to_income": 0.20,
            "income_cv": 0.30,
            "avg_savings_rate": 0.25,
            "avg_discretionary_ratio": 0.30,
        }
    )
    assert label_segment(row) == "Debt pressure"


def test_label_segment_falls_back_to_balanced_user():
    row = pd.Series(
        {
            "avg_debt_to_income": 0.05,
            "income_cv": 0.05,
            "avg_savings_rate": 0.10,
            "avg_discretionary_ratio": 0.10,
        }
    )
    assert label_segment(row) == "Balanced user"


def test_label_segment_detects_stable_saver():
    row = pd.Series(
        {
            "avg_debt_to_income": 0.05,
            "income_cv": 0.05,
            "avg_savings_rate": 0.25,
            "avg_discretionary_ratio": 0.10,
        }
    )
    assert label_segment(row) == "Stable saver"
