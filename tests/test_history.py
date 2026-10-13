import pandas as pd
import pytest

from swiss_financial_health.data_generation import generate_synthetic_transactions
from swiss_financial_health.features import build_monthly_features, build_user_summary
from swiss_financial_health.history import compute_score_history
from swiss_financial_health.scoring import compute_financial_health_score


@pytest.fixture(scope="module")
def monthly():
    return build_monthly_features(generate_synthetic_transactions(n_users=12, periods=6, seed=3))


def test_score_history_has_one_point_per_user_and_month(monthly):
    history = compute_score_history(monthly)
    assert len(history) == monthly["user_id"].nunique() * monthly["month"].nunique()
    assert history["financial_health_score"].between(0, 100).all()


def test_last_month_of_history_matches_the_full_period_score(monthly):
    history = compute_score_history(monthly)
    last = history.loc[history["month"] == history["month"].max()].set_index("user_id")
    current = compute_financial_health_score(build_user_summary(monthly)).set_index("user_id")
    pd.testing.assert_series_equal(
        last["financial_health_score"], current["financial_health_score"], check_names=False
    )
