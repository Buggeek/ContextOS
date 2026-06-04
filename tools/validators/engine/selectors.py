from __future__ import annotations

from engine.rule_registry import categories, rule_ids


def parse_rule_selector(selector: str | None) -> tuple[set[str], str | None]:
    available = rule_ids()
    available_categories = categories()
    if not selector or selector.strip() in {"", "all", "*"}:
        return set(available), None

    selected: set[str] = set()
    saw_positive = False
    tokens = [token.strip() for token in selector.split(",") if token.strip()]
    for raw_token in tokens:
        exclude = raw_token.startswith("-")
        token = raw_token[1:] if exclude else raw_token
        matches: set[str]
        if token in {"all", "*"}:
            matches = set(available)
        elif token.endswith(".*"):
            category = token[:-2]
            if category not in available_categories:
                return set(), f"Unknown rule category '{category}'."
            matches = {rule_id for rule_id in available if rule_id.startswith(f"{category}.")}
        elif token in available_categories:
            matches = {rule_id for rule_id in available if rule_id.startswith(f"{token}.")}
        elif token in available:
            matches = {token}
        else:
            return set(), f"Unknown rule selector '{token}'."

        if exclude:
            if not saw_positive and not selected:
                selected = set(available)
            selected -= matches
        else:
            saw_positive = True
            selected |= matches

    if not selected:
        return set(), "Rule selector disabled every rule."
    return selected, None
