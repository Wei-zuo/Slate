"""Compile structured shots into model-ready `ShotRenderRequest`.

The compiler does three things:

1. Resolve names and simple coreference against `AssetLibrary`
2. Bind image-reference slots under `ModelProfile` constraints
3. Render a `ShotRenderRequest` with positive/negative text plus references
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .assets import Asset, AssetLibrary
from .schemas import ImageRefSlot, ModelProfile, ProjectBrief, Shot, ShotRenderRequest, StoryboardPackage


PRONOUN_ROLE_HINTS = {
    "他": "character",
    "她": "character",
    "它": "non_character",
}


@dataclass(frozen=True)
class Mention:
    """Resolved mention span."""

    asset: Asset
    start: int
    end: int
    kind: str


def _first_asset_span(text: str, asset: Asset) -> tuple[int, int] | None:
    candidates = [asset.name, *asset.aliases]
    best: tuple[int, int] | None = None
    lowered = text.casefold()
    for candidate in candidates:
        candidate_lower = candidate.casefold()
        if candidate_lower.isascii() and re.fullmatch(r"[a-z0-9_\- ]+", candidate_lower):
            pattern = re.compile(rf"\b{re.escape(candidate_lower)}\b")
            match = pattern.search(lowered)
            if match is not None:
                span = (match.start(), match.end())
                if best is None or span[0] < best[0]:
                    best = span
        else:
            index = lowered.find(candidate_lower)
            if index != -1:
                span = (index, index + len(candidate))
                if best is None or span[0] < best[0]:
                    best = span
    return best


def _resolve_mentions(shot: Shot, library: AssetLibrary) -> list[Mention]:
    """Resolve explicit asset mentions and simple pronoun coreference."""

    explicit_assets = library.resolve_name(shot.description)
    mentions: list[Mention] = []
    for asset in explicit_assets:
        span = _first_asset_span(shot.description, asset)
        if span is not None:
            mentions.append(Mention(asset=asset, start=span[0], end=span[1], kind="explicit"))

    involved_assets = [library.get(asset_id) for asset_id in shot.involved_asset_ids]
    fallback_assets = [asset for asset in involved_assets if asset is not None]

    for match in re.finditer(r"[他她它]", shot.description):
        pronoun = match.group(0)
        role_hint = PRONOUN_ROLE_HINTS[pronoun]
        candidates = [mention for mention in mentions if mention.start < match.start()]
        if role_hint == "character":
            filtered = [mention for mention in candidates if mention.asset.asset_type == "character"]
        else:
            filtered = [mention for mention in candidates if mention.asset.asset_type != "character"]
        antecedent = (filtered or candidates)[-1] if (filtered or candidates) else None
        if antecedent is None and fallback_assets:
            if role_hint == "character":
                preferred = [asset for asset in fallback_assets if asset.asset_type == "character"]
            else:
                preferred = [asset for asset in fallback_assets if asset.asset_type != "character"]
            asset = (preferred or fallback_assets)[0]
            antecedent = Mention(asset=asset, start=match.start(), end=match.end(), kind="fallback")
        if antecedent is not None:
            mentions.append(
                Mention(
                    asset=antecedent.asset,
                    start=match.start(),
                    end=match.end(),
                    kind="coref",
                )
            )

    mentions.sort(key=lambda item: (item.start, item.end))
    return mentions


def _unique_assets_in_order(mentions: list[Mention], shot: Shot, library: AssetLibrary) -> list[Asset]:
    ordered: list[Asset] = []
    seen: set[str] = set()
    for mention in mentions:
        if mention.asset.asset_id in seen:
            continue
        seen.add(mention.asset.asset_id)
        ordered.append(mention.asset)
    for asset_id in shot.involved_asset_ids:
        asset = library.get(asset_id)
        if asset is None or asset.asset_id in seen:
            continue
        seen.add(asset.asset_id)
        ordered.append(asset)
    return ordered


def _asset_summary(asset: Asset) -> str:
    hooks = ", ".join(asset.visual_hooks[:3])
    if hooks:
        return f"{asset.name}: {asset.description}; visual hooks: {hooks}"
    return f"{asset.name}: {asset.description}"


def _camera_phrase(shot: Shot, model_profile: ModelProfile) -> str:
    movement = model_profile.camera_verb_map.get(shot.camera.movement, shot.camera.movement)
    parts = [movement, shot.camera.shot_size, shot.camera.position]
    if shot.camera.speed:
        parts.append(f"speed {shot.camera.speed}")
    return ", ".join(part for part in parts if part)


def compile_shot(
    shot: Shot,
    library: AssetLibrary,
    model_profile: ModelProfile,
    brief: ProjectBrief,
) -> ShotRenderRequest:
    """Compile one `Shot` into a `ShotRenderRequest`.

    Example:
        >>> from .model_profile import EXAMPLE_PROFILE
        >>> from .schemas import CameraSpec
        >>> request = compile_shot(
        ...     Shot(
        ...         shot_id='shot-01',
        ...         beat_id='beat-01',
        ...         duration_seconds=4,
        ...         description='鲁班抬头，他看向桥腹。',
        ...         involved_asset_ids=[],
        ...         camera=CameraSpec(movement='缓推', shot_size='medium', position='front'),
        ...         style_pack_id='style-pack',
        ...         risk_level='low',
        ...         notes='',
        ...     ),
        ...     library,
        ...     EXAMPLE_PROFILE,
        ...     brief,
        ... )
        >>> request.shot_id
        'shot-01'
    """

    if brief.aspect_ratio not in model_profile.aspect_ratios_supported:
        raise ValueError(
            f"Aspect ratio {brief.aspect_ratio!r} is not supported by model {model_profile.model_id!r}."
        )

    mentions = _resolve_mentions(shot, library)
    ordered_assets = _unique_assets_in_order(mentions, shot, library)
    style_pack = library.get(shot.style_pack_id)

    reference_candidates = [
        asset
        for asset in ordered_assets
        if asset.asset_type not in {"style_pack", "camera_pack"}
        and asset.reference_image_paths
        and asset.status in {"generated", "approved"}
    ]
    ref_assets = reference_candidates[: model_profile.max_ref_images]
    ref_asset_ids = {asset.asset_id for asset in ref_assets}

    ref_images = [
        ImageRefSlot(
            role=asset.asset_type if model_profile.role_binding_supported else f"ref_{index + 1}",
            asset_id=asset.asset_id,
            image_path=asset.reference_image_paths[0],
            slot_hint=asset.name if not model_profile.role_binding_supported else None,
        )
        for index, asset in enumerate(ref_assets)
    ]

    text_only_assets = [asset for asset in ordered_assets if asset.asset_id not in ref_asset_ids]
    positive_parts: list[str] = []
    if style_pack is not None:
        positive_parts.append(_asset_summary(style_pack))
    if ref_assets and not model_profile.role_binding_supported:
        positive_parts.append(
            "Reference subjects: " + "; ".join(_asset_summary(asset) for asset in ref_assets)
        )
    if text_only_assets:
        positive_parts.append("Asset notes: " + "; ".join(_asset_summary(asset) for asset in text_only_assets))
    positive_parts.append(f"Shot: {shot.description}")
    positive_parts.append(f"Camera: {_camera_phrase(shot, model_profile)}")

    return ShotRenderRequest(
        shot_id=shot.shot_id,
        target_model=model_profile.model_id,
        positive_text=" | ".join(part for part in positive_parts if part),
        negative_text=", ".join(model_profile.required_negative_fragments),
        ref_images=ref_images,
        first_frame_ref_path=shot.first_frame_ref.image_path if shot.first_frame_ref else None,
        last_frame_ref_path=shot.last_frame_ref.image_path if shot.last_frame_ref else None,
        camera=shot.camera,
        duration_seconds=shot.duration_seconds,
        aspect_ratio=brief.aspect_ratio,
        style_pack_id=shot.style_pack_id,
    )


def compile_all_shots(
    storyboard: StoryboardPackage,
    library: AssetLibrary,
    model_profile: ModelProfile,
    brief: ProjectBrief,
) -> list[ShotRenderRequest]:
    """Compile every shot in a storyboard package."""

    return [
        compile_shot(shot=shot, library=library, model_profile=model_profile, brief=brief)
        for shot in storyboard.shots
    ]
