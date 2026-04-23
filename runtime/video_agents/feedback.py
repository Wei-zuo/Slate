"""Keyword-based feedback parsing stub for Slate v0.3.

This module intentionally stays simple in v0.3. A later version can replace
the heuristics with an LLM-backed parser without changing the outer contract.
"""

from __future__ import annotations

from .assets import AssetLibrary
from .schemas import FeedbackItem


def parse_feedback(comment: str, library: AssetLibrary) -> list[FeedbackItem]:
    """Parse one human comment into one coarse `FeedbackItem`.

    Example:
        >>> library = AssetLibrary(__import__('pathlib').Path('/tmp/missing'))
        >>> parse_feedback('重新画鲁班', library)[0].change_type
        'regenerate'
    """

    comment_lower = comment.casefold()
    if any(token in comment for token in ("重新画", "重生", "重画")):
        change_type = "regenerate"
    elif any(token in comment for token in ("换图", "换参考")):
        change_type = "ref_swap"
    elif any(token in comment for token in ("颜色", "色调", "配色")):
        change_type = "palette_shift"
    elif any(token in comment for token in ("改一下", "改成", "不对", "不像")):
        change_type = "hook_edit"
    else:
        change_type = "description_edit"

    matches = library.resolve_name(comment)
    return [
        FeedbackItem(
            target_asset_id=matches[0].asset_id if matches else None,
            change_type=change_type,
            original_comment=comment,
            params={"normalized_comment": comment_lower},
        )
    ]
