from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schemas import AdFeedback, ArtPackage, ProductionPacket, ProjectBrief, StoryboardPackage, StoryPackage
from .state import VideoAgentState


@dataclass(frozen=True)
class StoryboardReviewResult:
    storyboard: StoryboardPackage
    feedback: AdFeedback


class VideoAgentServices(Protocol):
    """Provider-specific agent implementations plugged into the state graph."""

    def normalize_brief(self, state: VideoAgentState) -> ProjectBrief:
        ...

    def write_story_package(self, brief: ProjectBrief, state: VideoAgentState) -> StoryPackage:
        ...

    def write_art_package(self, brief: ProjectBrief, story: StoryPackage, state: VideoAgentState) -> ArtPackage:
        ...

    def review_storyboard(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        art: ArtPackage,
        state: VideoAgentState,
    ) -> StoryboardReviewResult:
        ...

    def integrate_packet(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        art: ArtPackage,
        storyboard: StoryboardPackage,
        state: VideoAgentState,
    ) -> ProductionPacket:
        ...

    def run_production(self, packet: ProductionPacket, state: VideoAgentState) -> None:
        ...
