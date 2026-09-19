"""Back-compat wrappers — correlation engine owns clustering now."""

from .correlation import build_relationships, linked_for_case, refresh_clusters


def linked_ids(case_id: str, cases: list[dict]) -> list[str]:
    rels = build_relationships(cases)
    return [item["case_id"] for item in linked_for_case(case_id, rels)]


__all__ = ["refresh_clusters", "linked_ids", "build_relationships", "linked_for_case"]
