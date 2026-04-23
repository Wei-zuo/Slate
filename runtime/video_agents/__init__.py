"""Slate v0.3 OpenClaw runtime exports."""

from .assets import Asset, AssetLibrary
from .compile import compile_all_shots, compile_shot
from .graph import build_video_agent_graph
from .model_profile import EXAMPLE_PROFILE

__all__ = [
    "Asset",
    "AssetLibrary",
    "EXAMPLE_PROFILE",
    "build_video_agent_graph",
    "compile_all_shots",
    "compile_shot",
]
