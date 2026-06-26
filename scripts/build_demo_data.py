from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swiss_financial_health.clustering import fit_user_segments
from swiss_financial_health.data_generation import generate_synthetic_transactions
from swiss_financial_health.features import build_monthly_features, build_user_summary
from swiss_financial_health.recommendations import generate_recommendations
from swiss_financial_health.scoring import compute_financial_health_score


DATA = ROOT / "data"


def main() -> None:
    DATA.mkdir(exist_ok=True)

    transactions = generate_synthetic_transactions(n_users=150, periods=12, seed=21)
    monthly_features = build_monthly_features(transactions)
    user_summary = build_user_summary(monthly_features)
    scored_users = compute_financial_health_score(user_summary)
    segmented_users, centroids, silhouette = fit_user_segments(scored_users, n_clusters=5)
    recommendations = generate_recommendations(segmented_users)

    transactions.to_csv(DATA / "synthetic_transactions.csv", index=False)
    monthly_features.to_csv(DATA / "user_monthly_features.csv", index=False)
    segmented_users.to_csv(DATA / "scored_users.csv", index=False)
    recommendations.to_csv(DATA / "recommendations.csv", index=False)
    centroids.to_csv(DATA / "segment_centroids.csv", index=False)

    print(f"Generated {len(transactions):,} synthetic transactions")
    print(f"Generated {len(segmented_users):,} user profiles")
    print(f"Silhouette score: {silhouette:.3f}")


if __name__ == "__main__":
    main()
