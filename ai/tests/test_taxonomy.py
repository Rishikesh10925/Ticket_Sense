from benchmark.taxonomy import load_taxonomy, validate


def test_taxonomy_is_valid_and_covers_every_existing_article():
    tax = load_taxonomy()
    assert validate(tax) == []
    assert len(tax.topics) == 30
    assert len(tax.served()) * tax.articles_per_topic == 96
    assert len(tax.withheld()) * tax.articles_per_topic == 24


def test_authoring_split_matches_blueprint():
    tax = load_taxonomy()
    per_author = {a: sum(1 for t in tax.topics if t.author == a) * tax.articles_per_topic for a in "RAS"}
    assert per_author == {"S": 48, "R": 36, "A": 36}


def test_article_ids():
    assert load_taxonomy().topic("net-vpn").article_id(3) == "NET-VPN-003"
