"""Outcome-blind period assessment from observed article/source coverage."""
from collections import Counter


INSTITUTIONAL_DOMAINS = {"analdex.org"}
PRIMARY_PRESS_DOMAINS = {"valoraanalitik.com", "larepublica.co"}


def is_press(row):
    return row.get("publisher_group", "") not in INSTITUTIONAL_DOMAINS


def in_primary_press_frame(row):
    return row.get("discovery_source") == "publisher_declared_sitemap" and row.get("publisher_group") in PRIMARY_PRESS_DOMAINS


def coverage_table(rows, months):
    eligible = [r for r in rows if r.get("eligible_for_index")]
    result = []
    for month in months:
        subset = [r for r in eligible if r["month"] == month]
        press = [r for r in subset if in_primary_press_frame(r)]
        sources = Counter(r["publisher_group"] for r in press)
        result.append({"month": month, "press_articles": len(press), "press_domains": len(sources),
            "institutional_articles": sum(not is_press(r) for r in subset),
            "complementary_press_articles": sum(is_press(r) and not in_primary_press_frame(r) for r in subset),
            "press_source_counts": dict(sorted(sources.items())),
            "largest_press_source_share": max(sources.values())/len(press) if press else None,
            "statistical_reporting_candidates": sum(r.get("document_role_proposal") in {"statistical_reporting_candidate", "mixed_cues"} for r in press),
            "unresolved_document_roles": sum(r.get("document_role_proposal") == "unresolved" for r in press),
            "human_reviewed_articles": sum(r.get("review_status") == "human_reviewed" for r in press)})
    return result


def longest_window(table, minimum_articles=3, minimum_domains=2):
    """Choose the longest qualifying calendar run; tie goes to earliest run.

    Inputs must enumerate every consecutive calendar month. No outcome, score or
    export value is consulted. These are transparent design thresholds, not a
    validated claim of representativeness or sufficient statistical power.
    """
    ordinal = [12*int(r["month"][:4])+int(r["month"][5:7]) for r in table]
    if any(right-left != 1 for left, right in zip(ordinal, ordinal[1:])):
        raise ValueError("Coverage must enumerate consecutive calendar months, including empty months")
    best, current = [], []
    for row in table:
        if row["press_articles"] >= minimum_articles and row["press_domains"] >= minimum_domains:
            current.append(row["month"])
            if len(current) > len(best):
                best = list(current)
        else:
            current = []
    return {"start": best[0] if best else None, "end_inclusive": best[-1] if best else None,
            "months": len(best), "minimum_press_articles": minimum_articles, "minimum_press_domains": minimum_domains}


def assess(rows, months):
    table = coverage_table(rows, months)
    # A one-source month contains observations; it is not an empty month. Require
    # continuous article support and >=95% two-source months, with strict-panel
    # sensitivity retained instead of discarding later years at one sparse month.
    best = []
    for left in range(len(table)):
        for right in range(left+1, len(table)+1):
            window = table[left:right]
            if all(r["press_articles"] >= 3 and r["press_domains"] >= 1 for r in window) and sum(r["press_domains"] >= 2 for r in window)/len(window) >= .95:
                if len(window) > len(best):
                    best = window
    selected = {"start": best[0]["month"] if best else None, "end_inclusive": best[-1]["month"] if best else None,
                "months": len(best), "minimum_press_articles": 3, "minimum_press_domains": 1,
                "required_two_domain_month_share": .95, "two_domain_months": sum(r["press_domains"] >= 2 for r in best),
                "single_domain_months": [r["month"] for r in best if r["press_domains"] == 1]}
    return {"selection_uses_export_outcomes": False, "selection_uses_sentiment_scores": False,
            "primary_press_domains": sorted(PRIMARY_PRESS_DOMAINS),
            "primary_frame": "Direct publisher-declared sitemap acquisition from two economic-news domains; institutional and legacy Google routes remain complementary.",
            "status": "coverage_assessment_not_human_or_economic_validation",
            "rule": "Longest complete calendar run with >=3 eligible press articles per month, >=1 domain every month and >=2 domains in >=95% of months; earliest tie.",
            "main_window": selected,
            "strict_two_domain_window": longest_window(table),
            "threshold_sensitivity": [longest_window(table, n) for n in (1, 3, 5)],
            "monthly": table,
            "interpretation": "Thresholds describe observed sampling support only. Publisher domains do not identify independent ownership; institutional reports stay separate. A long supported window does not prove predictive power."}
