from swiss_financial_health.clustering import fit_user_segments
from swiss_financial_health.credit_readiness import build_risk_flags, compute_credit_readiness
from swiss_financial_health.data_generation import generate_synthetic_transactions
from swiss_financial_health.features import build_monthly_features, build_user_summary
from swiss_financial_health.recommendations import generate_recommendations
from swiss_financial_health.scoring import compute_financial_health_score


def test_end_to_end_pipeline_produces_scores_and_recommendations():
    transactions = generate_synthetic_transactions(n_users=20, periods=6, seed=7)
    monthly = build_monthly_features(transactions)
    summary = build_user_summary(monthly)
    scored = compute_financial_health_score(summary)
    credit = compute_credit_readiness(scored)
    segmented, centroids, silhouette = fit_user_segments(credit, n_clusters=4)
    recommendations = generate_recommendations(segmented)
    risk_flags = build_risk_flags(segmented)

    assert len(transactions) > 0
    assert len(scored) == 20
    assert scored["financial_health_score"].between(0, 100).all()
    assert credit["credit_readiness_score"].between(0, 100).all()
    assert credit["credit_readiness_band"].notna().all()
    assert segmented["segment_label"].notna().all()
    assert len(centroids) == 4
    assert -1 <= silhouette <= 1
    assert len(recommendations) == 20
    assert risk_flags["user_id"].nunique() == 20
