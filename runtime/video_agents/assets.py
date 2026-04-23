"""Asset schemas and disk-backed asset library for Slate.

The AssetLibrary is the shared memory surface for the six-agent workflow.

Example:
    >>> from pathlib import Path
    >>> library = AssetLibrary(Path('/tmp/slate-assets'))
    >>> library.add(Asset(
    ...     asset_id='luban',
    ...     asset_type='character',
    ...     name='鲁班',
    ...     aliases=['鲁师傅'],
    ...     description='木石工匠',
    ...     visual_hooks=['石锤', '粗布短衫'],
    ...     reference_image_paths=[],
    ...     status='stub',
    ...     created_by_phase='producer_intake',
    ...     created_by_agent='producer',
    ...     notes='',
    ... ))
    >>> library.find_by_name('鲁班').asset_id
    'luban'
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml

from .schemas import StrictModel


AssetType = Literal["character", "location", "prop", "style_pack", "camera_pack"]
AssetStatus = Literal["stub", "generated", "approved", "rejected"]
ASSET_TYPES: tuple[AssetType, ...] = ("character", "location", "prop", "style_pack", "camera_pack")


class Asset(StrictModel):
    """Single asset tracked in the shared library."""

    asset_id: str
    asset_type: AssetType
    name: str
    aliases: list[str]
    description: str
    visual_hooks: list[str]
    reference_image_paths: list[str]
    status: AssetStatus
    created_by_phase: str
    created_by_agent: str
    notes: str = ""


class AssetLibrary:
    """Disk-backed asset registry used by all Slate runtime nodes."""

    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.assets: dict[str, Asset] = {}

    def load(self) -> "AssetLibrary":
        """Load all asset metadata from disk."""

        self.assets = {}
        if not self.root_path.exists():
            return self
        for asset_type in ASSET_TYPES:
            type_dir = self.root_path / asset_type
            if not type_dir.exists():
                continue
            for meta_path in type_dir.glob("*/meta.yaml"):
                payload = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
                asset = Asset.model_validate(payload)
                self.assets[asset.asset_id] = asset
        return self

    def save(self) -> None:
        """Persist all in-memory asset metadata to disk."""

        self.root_path.mkdir(parents=True, exist_ok=True)
        for asset in self.assets.values():
            asset_dir = self.root_path / asset.asset_type / asset.asset_id
            asset_dir.mkdir(parents=True, exist_ok=True)
            meta_path = asset_dir / "meta.yaml"
            meta_path.write_text(
                yaml.safe_dump(asset.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

    def add(self, asset: Asset) -> None:
        """Add or replace an asset."""

        self.assets[asset.asset_id] = asset

    def get(self, asset_id: str) -> Asset | None:
        """Return an asset by id."""

        return self.assets.get(asset_id)

    def find_by_name(self, name: str) -> Asset | None:
        """Return the first asset whose name matches exactly, case-insensitively."""

        lowered = name.casefold()
        for asset in self.assets.values():
            if asset.name.casefold() == lowered:
                return asset
        return None

    def find_by_alias(self, alias: str) -> Asset | None:
        """Return the first asset whose alias matches exactly, case-insensitively."""

        lowered = alias.casefold()
        for asset in self.assets.values():
            if any(candidate.casefold() == lowered for candidate in [asset.name, *asset.aliases]):
                return asset
        return None

    def list_by_type(self, asset_type: AssetType) -> list[Asset]:
        """List all assets of one type."""

        return [asset for asset in self.assets.values() if asset.asset_type == asset_type]

    def update_status(self, asset_id: str, new_status: AssetStatus) -> None:
        """Update an asset status in memory."""

        asset = self.assets[asset_id]
        asset.status = new_status

    def resolve_name(self, text: str) -> list[Asset]:
        """Return assets whose names or aliases are mentioned in `text`.

        Matches are deduplicated and sorted by first appearance.
        """

        hits: list[tuple[int, Asset]] = []
        lowered = text.casefold()
        for asset in self.assets.values():
            first_index: int | None = None
            for candidate in [asset.name, *asset.aliases]:
                index = self._find_candidate_index(lowered, candidate)
                if index is not None and (first_index is None or index < first_index):
                    first_index = index
            if first_index is not None:
                hits.append((first_index, asset))
        hits.sort(key=lambda item: item[0])
        seen: set[str] = set()
        ordered: list[Asset] = []
        for _, asset in hits:
            if asset.asset_id in seen:
                continue
            seen.add(asset.asset_id)
            ordered.append(asset)
        return ordered

    def _find_candidate_index(self, lowered_text: str, candidate: str) -> int | None:
        candidate_lower = candidate.casefold()
        if not candidate_lower:
            return None
        if candidate_lower.isascii() and re.fullmatch(r"[a-z0-9_\- ]+", candidate_lower):
            pattern = re.compile(rf"\b{re.escape(candidate_lower)}\b")
            match = pattern.search(lowered_text)
            return None if match is None else match.start()
        index = lowered_text.find(candidate_lower)
        return None if index == -1 else index
