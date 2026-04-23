"""Service protocols for the Slate v0.3 runtime.

The runtime graph only depends on these protocols. Real OpenClaw integrations
can swap in model-backed implementations later, while `stubs.py` provides the
minimal runnable versions used by tests and the demo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .assets import Asset, AssetLibrary
from .schemas import (
    AdFeedback,
    ArtGenerationPlan,
    ImageJob,
    ProductionPacket,
    ProjectBrief,
    StoryPackage,
    StoryboardPackage,
    VideoJob,
)
from .state import VideoAgentState


class ProducerAgent(Protocol):
    """Producer contract."""

    def normalize_brief(self, state: VideoAgentState) -> ProjectBrief:
        """Freeze or normalize the project brief."""

    def bootstrap_stub_assets(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
    ) -> list[Asset]:
        """Create stub assets after the screenwriter finishes."""

    def integrate_packet(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        art: ArtGenerationPlan,
        storyboard: StoryboardPackage,
        state: VideoAgentState,
    ) -> ProductionPacket:
        """Assemble the final production packet."""


class ScreenwriterAgent(Protocol):
    """Screenwriter contract."""

    def write_story_package(self, brief: ProjectBrief, state: VideoAgentState) -> StoryPackage:
        """Produce the structured story package."""


class ArtDesignAgent(Protocol):
    """Art-design contract."""

    def plan_art_generation(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
        state: VideoAgentState,
    ) -> ArtGenerationPlan:
        """Return the style pack id and queued asset-image jobs."""


class AssistantDirectorAgent(Protocol):
    """Assistant-director contract."""

    def cut_storyboard(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
        state: VideoAgentState,
    ) -> tuple[StoryboardPackage, list[ImageJob]]:
        """Cut storyboard shots and emit first/last-frame image jobs."""

    def review_storyboard(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
        storyboard: StoryboardPackage,
        state: VideoAgentState,
    ) -> AdFeedback:
        """Return the AD decision."""


class ImageProductionAgent(Protocol):
    """Image-production contract."""

    def process_image_job(self, job: ImageJob, library: AssetLibrary) -> ImageJob:
        """Process one queued image job."""


class VideoProductionAgent(Protocol):
    """Video-production contract."""

    def process_video_job(self, job: VideoJob) -> VideoJob:
        """Process one queued video job."""


@dataclass(frozen=True)
class VideoAgentServices:
    """Concrete service bundle plugged into the graph."""

    producer: ProducerAgent
    screenwriter: ScreenwriterAgent
    art_design: ArtDesignAgent
    assistant_director: AssistantDirectorAgent
    image_production: ImageProductionAgent
    video_production: VideoProductionAgent
