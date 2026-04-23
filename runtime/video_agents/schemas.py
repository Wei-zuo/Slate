"""Pydantic schemas for the Slate v0.3 OpenClaw plugin runtime.

The models in this module are the machine-readable contracts passed between
the six agents described in `skills/video-agent-orchestration/`.

Example:
    >>> brief = ProjectBrief(
    ...     project_id="demo-001",
    ...     route=InputRoute.NEW_BRIEF,
    ...     title="赵州桥试桥",
    ...     goal="把 brief 推进到可渲染分镜请求",
    ...     platform="OpenClaw",
    ...     format="2D animation short",
    ...     target_duration_seconds=60,
    ...     language="zh-CN",
    ...     delivery_scope="shot render requests",
    ... )
    >>> brief.aspect_ratio
    '16:9'
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model that rejects undeclared fields."""

    model_config = ConfigDict(extra="forbid")


class InputRoute(str, Enum):
    """Entry routes handled by the producer."""

    NEW_BRIEF = "new_brief"
    EXISTING_SCRIPT = "existing_script"
    ADAPTATION = "adaptation"
    PRODUCTION_RESCUE = "production_rescue"


class ProjectBrief(StrictModel):
    """Producer-frozen project brief."""

    project_id: str
    route: InputRoute
    title: str
    goal: str
    platform: str = "OpenClaw"
    format: str
    target_duration_seconds: int = Field(ge=1)
    language: str
    aspect_ratio: str = "16:9"
    target_audience: list[str] = Field(default_factory=list)
    source_materials: list[str] = Field(default_factory=list)
    required_elements: list[str] = Field(default_factory=list)
    forbidden_drift: list[str] = Field(default_factory=list)
    delivery_scope: str


class CharacterCard(StrictModel):
    """Character summary passed from screenwriter to producer/art design."""

    character_id: str
    name: str
    dramatic_function: str
    visual_hooks: list[str] = Field(default_factory=list)
    asset_hint: str


class StoryBeat(StrictModel):
    """Narrative beat used for storyboarding and beat-aware segmentation."""

    beat_id: str
    scene_id: str
    order: int = Field(ge=1)
    label: str
    purpose: str
    summary: str
    duration_seconds: float = Field(gt=0)


class SceneSpec(StrictModel):
    """Scene-level grouping for beats and shots."""

    scene_id: str
    order: int = Field(ge=1)
    title: str
    location: str
    time_of_day: str
    summary: str
    involved_characters: list[str] = Field(default_factory=list)
    target_shot_count: int = Field(ge=1)


class StoryPackage(StrictModel):
    """Structured screenwriter output."""

    title: str
    logline: str
    synopsis: str
    adaptation_goal: str
    format: str
    emotional_rhythm: list[str] = Field(default_factory=list)
    characters: list[CharacterCard] = Field(default_factory=list)
    scenes: list[SceneSpec] = Field(default_factory=list)
    beats: list[StoryBeat] = Field(default_factory=list)
    estimated_total_shots: int = Field(ge=1)
    narration_style: str
    dialogue_constraints: list[str] = Field(default_factory=list)
    visual_motifs: list[str] = Field(default_factory=list)
    notes: str = ""


class CameraSpec(StrictModel):
    """Camera instruction normalized for prompt compilation."""

    movement: str
    shot_size: str
    position: str
    speed: Literal["slow", "medium", "fast"] | None = None


class FrameRef(StrictModel):
    """Reference slot for a shot boundary frame."""

    source: Literal["asset", "to_generate"]
    asset_id: str | None = None
    generation_hint: str | None = None
    image_path: str | None = None


class Shot(StrictModel):
    """Executable shot spec produced by the assistant director."""

    shot_id: str
    beat_id: str
    duration_seconds: float
    description: str
    involved_asset_ids: list[str]
    camera: CameraSpec
    first_frame_ref: FrameRef | None = None
    last_frame_ref: FrameRef | None = None
    style_pack_id: str
    risk_level: Literal["low", "medium", "high"]
    notes: str


class ImageJob(StrictModel):
    """Queue item consumed by the image-production agent."""

    job_id: str
    job_kind: Literal["asset_image", "first_frame", "last_frame"]
    target_asset_id: str | None = None
    target_shot_id: str | None = None
    prompt: str
    negative_prompt: str
    reference_image_paths: list[str] = Field(default_factory=list)
    aspect_ratio: str
    style_pack_id: str | None = None
    status: Literal["pending", "in_progress", "done", "failed"] = "pending"
    output_image_path: str | None = None
    retry_count: int = 0
    error: str | None = None


class ArtGenerationPlan(StrictModel):
    """Art-design output handed to the image-production queue."""

    style_pack_id: str
    asset_jobs: list[ImageJob]
    notes: str = ""


class ImageRefSlot(StrictModel):
    """Bound image reference passed to a target render model."""

    role: str
    asset_id: str
    image_path: str
    slot_hint: str | None = None


class ShotRenderRequest(StrictModel):
    """Final per-shot request compiled for a downstream video model."""

    shot_id: str
    target_model: str
    positive_text: str
    negative_text: str
    ref_images: list[ImageRefSlot]
    first_frame_ref_path: str | None = None
    last_frame_ref_path: str | None = None
    camera: CameraSpec
    duration_seconds: float
    aspect_ratio: str
    style_pack_id: str | None = None


class VideoJob(StrictModel):
    """Queue item consumed by the video-production agent."""

    job_id: str
    shot_id: str
    render_request: ShotRenderRequest
    status: Literal["pending", "in_progress", "done", "failed"] = "pending"
    output_video_path: str | None = None
    retry_count: int = 0
    error: str | None = None


class ModelProfile(StrictModel):
    """Capability descriptor injected by OpenClaw for the target model."""

    model_id: str
    max_seconds: float
    max_ref_images: int
    role_binding_supported: bool
    required_negative_fragments: list[str] = Field(default_factory=list)
    camera_verb_map: dict[str, str] = Field(default_factory=dict)
    preferred_language: Literal["zh", "en", "either"] = "either"
    aspect_ratios_supported: list[str] = Field(default_factory=lambda: ["16:9"])


class Segment(StrictModel):
    """Beat-aware segment grouping used for batching/packing."""

    segment_id: str
    beat_ids: list[str]
    shot_ids: list[str]
    duration_seconds: float


class StoryboardPackage(StrictModel):
    """Structured AD output with executable shots and test priorities."""

    total_duration_seconds: float = Field(gt=0)
    shots: list[Shot] = Field(default_factory=list)
    continuity_notes: list[str] = Field(default_factory=list)
    first_test_shot_ids: list[str] = Field(default_factory=list)


class RevisionTarget(str, Enum):
    """Phase target for revision routing."""

    SCREENWRITER = "screenwriter"
    ART_DESIGN = "art_design"
    ASSISTANT_DIRECTOR = "assistant_director_cut"


class ReviewDecision(str, Enum):
    """Assistant-director review outcomes."""

    APPROVED = "approved"
    REVISE_STORY = "revise_story"
    REVISE_ART = "revise_art"
    REVISE_STORYBOARD = "revise_storyboard"
    BLOCKED = "blocked"


class RevisionRequest(StrictModel):
    """Structured feedback item used by the revision router."""

    target: RevisionTarget
    reason: str
    blocking_issues: list[str] = Field(default_factory=list)
    requested_changes: list[str] = Field(default_factory=list)
    retry_budget: int = Field(ge=0, default=0)


class AdFeedback(StrictModel):
    """AD review summary and rework decision."""

    decision: ReviewDecision
    summary: str
    blocking_issues: list[str] = Field(default_factory=list)
    high_risk_shot_ids: list[str] = Field(default_factory=list)
    first_test_shot_ids: list[str] = Field(default_factory=list)
    revision_request: RevisionRequest | None = None


class PriorityLevel(str, Enum):
    """Priority bands used in the production packet."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class ProductionTodoItem(StrictModel):
    """Concrete producer task after integration."""

    item_id: str
    priority: PriorityLevel
    owner_role: str
    description: str
    depends_on: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class FeedbackItem(StrictModel):
    """Parsed, machine-readable feedback change request."""

    target_asset_id: str | None = None
    target_shot_id: str | None = None
    change_type: Literal["regenerate", "hook_edit", "ref_swap", "palette_shift", "description_edit"]
    params: dict = Field(default_factory=dict)
    original_comment: str


class ProductionPacket(StrictModel):
    """Producer-integrated packet ready to feed video-production jobs."""

    brief: ProjectBrief
    story: StoryPackage
    art_generation_plan: ArtGenerationPlan
    storyboard: StoryboardPackage
    ad_feedback: AdFeedback | None = None
    locked_constraints: list[str] = Field(default_factory=list)
    render_requests: list[ShotRenderRequest] = Field(default_factory=list)
    segments: list[Segment] = Field(default_factory=list)
    todo_items: list[ProductionTodoItem] = Field(default_factory=list)
    summary: str = ""
