"""State objects for the Slate v0.3 LangGraph workflow.

Example:
    >>> from pathlib import Path
    >>> state = VideoAgentState(
    ...     phase=WorkflowPhase.PRODUCER_INTAKE,
    ...     asset_library_path=str(Path("/tmp/assets")),
    ... )
    >>> state["phase"]
    <WorkflowPhase.PRODUCER_INTAKE: 'producer_intake'>
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TypedDict

from pydantic import Field

from .schemas import (
    AdFeedback,
    ArtGenerationPlan,
    ModelProfile,
    ProductionPacket,
    ProjectBrief,
    RevisionRequest,
    StoryPackage,
    StoryboardPackage,
    StrictModel,
    VideoJob,
    ImageJob,
)


class WorkflowPhase(str, Enum):
    """Named workflow stages used by the graph router."""

    PRODUCER_INTAKE = "producer_intake"
    SCREENWRITER = "screenwriter"
    ART_DESIGN = "art_design"
    IMAGE_PRODUCTION = "image_production"
    ASSISTANT_DIRECTOR_CUT = "assistant_director_cut"
    ASSISTANT_DIRECTOR_REVIEW = "assistant_director_review"
    PRODUCER_INTEGRATION = "producer_integration"
    VIDEO_PRODUCTION = "video_production"
    DONE = "done"
    FAILED = "failed"


class RevisionCounter(StrictModel):
    """Per-stage revision counts."""

    screenwriter: int = 0
    art_design: int = 0
    assistant_director: int = 0

    def total(self) -> int:
        """Return the total revision count."""

        return self.screenwriter + self.art_design + self.assistant_director


class RevisionLimits(StrictModel):
    """Revision budget policy."""

    screenwriter: int = 2
    art_design: int = 2
    assistant_director: int = 1
    total: int = 5


class AuditEntry(StrictModel):
    """Audit log entry for node-level tracing."""

    phase: WorkflowPhase
    event: str
    detail: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VideoAgentState(TypedDict, total=False):
    """Mutable graph state passed between Slate runtime nodes."""

    phase: WorkflowPhase
    brief: ProjectBrief
    story_package: StoryPackage
    art_generation_plan: ArtGenerationPlan | None
    storyboard: StoryboardPackage
    ad_feedback: AdFeedback
    production_packet: ProductionPacket
    model_profile: ModelProfile
    active_revision: RevisionRequest | None
    revision_counts: RevisionCounter
    revision_limits: RevisionLimits
    stop_reason: str | None
    audit_log: list[AuditEntry]
    asset_library_path: str
    pending_image_jobs: list[ImageJob]
    pending_video_jobs: list[VideoJob]
    node_runs: dict[str, int]
