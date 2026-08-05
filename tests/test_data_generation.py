from swiss_financial_health.data_generation import generate_synthetic_transactions


def test_generate_synthetic_transactions_covers_every_user_and_month():
    transactions = generate_synthetic_transactions(n_users=5, periods=3, seed=1)
    assert transactions["user_id"].nunique() == 5
    assert transactions["date"].dt.to_period("M").nunique() == 3


def test_generate_synthetic_transactions_is_reproducible_for_same_seed():
    first = generate_synthetic_transactions(n_users=5, periods=3, seed=1)
    second = generate_synthetic_transactions(n_users=5, periods=3, seed=1)
    assert first.equals(second)


def test_generate_synthetic_transactions_differs_across_seeds():
    first = generate_synthetic_transactions(n_users=5, periods=3, seed=1)
    second = generate_synthetic_transactions(n_users=5, periods=3, seed=2)
    assert not first["amount_chf"].equals(second["amount_chf"])


def test_generate_synthetic_transactions_has_no_negative_amounts():
    transactions = generate_synthetic_transactions(n_users=10, periods=4, seed=3)
    assert (transactions["amount_chf"] >= 0).all()


def test_generate_synthetic_transactions_assigns_a_known_profile_to_every_user():
    from swiss_financial_health.data_generation import PROFILES

    transactions = generate_synthetic_transactions(n_users=10, periods=2, seed=3)
    profile_names = {profile.name for profile in PROFILES}
    assert set(transactions["profile"].unique()).issubset(profile_names)
