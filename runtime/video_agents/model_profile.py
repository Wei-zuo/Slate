"""ModelProfile helpers.

Real model capability profiles are injected by OpenClaw. Slate only defines the
interface and ships a placeholder profile for tests and demos.
"""

from __future__ import annotations

from .schemas import ModelProfile


EXAMPLE_PROFILE = ModelProfile(
    model_id="__example__",
    max_seconds=15.0,
    max_ref_images=1,
    role_binding_supported=False,
    required_negative_fragments=["no subtitles", "no watermark", "no logo"],
    camera_verb_map={"缓推": "slow dolly in", "侧移": "side truck", "跟随": "tracking shot"},
    preferred_language="either",
    aspect_ratios_supported=["16:9", "9:16"],
)
