"""Minimal runnable stub agents for tests and smoke demos."""

from __future__ import annotations

from pathlib import Path

from .assets import Asset, AssetLibrary
from .model_profile import EXAMPLE_PROFILE
from .schemas import (
    AdFeedback,
    ArtGenerationPlan,
    CameraSpec,
    CharacterCard,
    ImageJob,
    PriorityLevel,
    ProductionPacket,
    ProductionTodoItem,
    ProjectBrief,
    ReviewDecision,
    SceneSpec,
    Shot,
    StoryBeat,
    StoryPackage,
    StoryboardPackage,
    VideoJob,
)
from .services import VideoAgentServices
from .state import VideoAgentState


class StubProducerAgent:
    """Stub producer with deterministic outputs."""

    def normalize_brief(self, state: VideoAgentState) -> ProjectBrief:
        return ProjectBrief(
            project_id="stub-project",
            route="new_brief",
            title="Stub Project",
            goal="Exercise the Slate graph",
            platform="OpenClaw",
            format="2D short",
            target_duration_seconds=12,
            language="zh-CN",
            aspect_ratio="16:9",
            target_audience=["test"],
            delivery_scope="shot render requests",
        )

    def bootstrap_stub_assets(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
    ) -> list[Asset]:
        assets: list[Asset] = []
        for card in story.characters:
            if library.get(card.character_id) is None:
                assets.append(
                    Asset(
                        asset_id=card.character_id,
                        asset_type="character",
                        name=card.name,
                        aliases=[],
                        description=card.asset_hint,
                        visual_hooks=list(card.visual_hooks),
                        reference_image_paths=[],
                        status="stub",
                        created_by_phase="screenwriter",
                        created_by_agent="producer",
                        notes="bootstrap character",
                    )
                )
        if library.get("stub-location") is None:
            assets.append(
                Asset(
                    asset_id="stub-location",
                    asset_type="location",
                    name="赵州桥",
                    aliases=["大桥"],
                    description="主场景桥体",
                    visual_hooks=["石桥", "拱桥"],
                    reference_image_paths=[],
                    status="stub",
                    created_by_phase="screenwriter",
                    created_by_agent="producer",
                    notes="bootstrap location",
                )
            )
        if library.get("stub-style-pack") is None:
            assets.append(
                Asset(
                    asset_id="stub-style-pack",
                    asset_type="style_pack",
                    name="2D 国风风格包",
                    aliases=["国风风格"],
                    description="2D hand-drawn guofeng animation style pack",
                    visual_hooks=["青灰石色", "金色仙光"],
                    reference_image_paths=[],
                    status="stub",
                    created_by_phase="screenwriter",
                    created_by_agent="producer",
                    notes="bootstrap style pack",
                )
            )
        return assets

    def integrate_packet(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        art: ArtGenerationPlan,
        storyboard: StoryboardPackage,
        state: VideoAgentState,
    ) -> ProductionPacket:
        requests = [job.render_request for job in state.get("pending_video_jobs", [])]
        return ProductionPacket(
            brief=brief,
            story=story,
            art_generation_plan=art,
            storyboard=storyboard,
            ad_feedback=state.get("ad_feedback"),
            locked_constraints=["Keep story, art, and storyboard aligned."],
            render_requests=requests,
            segments=[],
            todo_items=[
                ProductionTodoItem(
                    item_id="todo-01",
                    priority=PriorityLevel.P0,
                    owner_role="video_production",
                    description="Render all approved shot requests.",
                    success_criteria=["All video jobs reach done state."],
                )
            ],
            summary=f"{len(requests)} render requests ready.",
        )


class StubScreenwriterAgent:
    """Stub screenwriter."""

    def write_story_package(self, brief: ProjectBrief, state: VideoAgentState) -> StoryPackage:
        return StoryPackage(
            title=brief.title,
            logline="鲁班造桥，张果老试桥，凡人托桥成传奇。",
            synopsis="一个最小可跑的赵州桥故事包。",
            adaptation_goal="Make the graph runnable.",
            format=brief.format,
            emotional_rhythm=["steady", "pressure", "release"],
            characters=[
                CharacterCard(
                    character_id="luban",
                    name="鲁班",
                    dramatic_function="hero craftsman",
                    visual_hooks=["石锤", "粗布短衫"],
                    asset_hint="壮年匠人，肩背有力",
                ),
                CharacterCard(
                    character_id="zhangguolao",
                    name="张果老",
                    dramatic_function="tester",
                    visual_hooks=["倒骑白驴", "斗笠"],
                    asset_hint="老者仙人，轻巧戏谑",
                ),
            ],
            scenes=[
                SceneSpec(
                    scene_id="scene-1",
                    order=1,
                    title="桥头",
                    location="赵州桥",
                    time_of_day="day",
                    summary="张果老试桥，鲁班迎接。",
                    involved_characters=["luban", "zhangguolao"],
                    target_shot_count=2,
                )
            ],
            beats=[
                StoryBeat(
                    beat_id="beat-1",
                    scene_id="scene-1",
                    order=1,
                    label="试桥开场",
                    purpose="set up",
                    summary="张果老来到桥头。",
                    duration_seconds=6,
                ),
                StoryBeat(
                    beat_id="beat-2",
                    scene_id="scene-1",
                    order=2,
                    label="托桥",
                    purpose="payoff",
                    summary="鲁班托桥稳住局面。",
                    duration_seconds=6,
                ),
            ],
            estimated_total_shots=2,
            narration_style="narration-led",
            visual_motifs=["stone", "gold light"],
        )


class StubArtDesignAgent:
    """Stub art-design agent."""

    def plan_art_generation(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
        state: VideoAgentState,
    ) -> ArtGenerationPlan:
        asset_jobs: list[ImageJob] = []
        for asset in sorted(library.assets.values(), key=lambda item: item.asset_id):
            if asset.asset_type == "camera_pack":
                continue
            asset_jobs.append(
                ImageJob(
                    job_id=f"img-{asset.asset_id}",
                    job_kind="asset_image",
                    target_asset_id=asset.asset_id,
                    prompt=f"Generate reference art for {asset.name}: {asset.description}",
                    negative_prompt="",
                    aspect_ratio=brief.aspect_ratio,
                    style_pack_id="stub-style-pack",
                )
            )
        return ArtGenerationPlan(
            style_pack_id="stub-style-pack",
            asset_jobs=asset_jobs,
            notes="stub art generation plan",
        )


class StubAssistantDirectorAgent:
    """Stub assistant director."""

    def cut_storyboard(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
        state: VideoAgentState,
    ) -> tuple[StoryboardPackage, list[ImageJob]]:
        shots = [
            Shot(
                shot_id="shot-01",
                beat_id="beat-1",
                duration_seconds=5,
                description="张果老骑驴来到赵州桥，他俯看桥身。",
                involved_asset_ids=["zhangguolao", "stub-location"],
                camera=CameraSpec(movement="缓推", shot_size="wide", position="front", speed="slow"),
                first_frame_ref={"source": "to_generate", "generation_hint": "桥头起始帧"},
                last_frame_ref={"source": "to_generate", "generation_hint": "进入桥面前的收帧"},
                style_pack_id="stub-style-pack",
                risk_level="medium",
                notes="test shot",
            ),
            Shot(
                shot_id="shot-02",
                beat_id="beat-2",
                duration_seconds=7,
                description="鲁班托住桥腹，他稳住桥身。",
                involved_asset_ids=["luban", "stub-location"],
                camera=CameraSpec(movement="跟随", shot_size="medium", position="low", speed="medium"),
                first_frame_ref={"source": "to_generate", "generation_hint": "托桥前一刻"},
                last_frame_ref={"source": "to_generate", "generation_hint": "桥稳住后的定格"},
                style_pack_id="stub-style-pack",
                risk_level="high",
                notes="test shot",
            ),
        ]
        frame_jobs = [
            ImageJob(
                job_id="first-shot-01",
                job_kind="first_frame",
                target_shot_id="shot-01",
                prompt="Generate first frame for shot 01",
                negative_prompt="",
                aspect_ratio=brief.aspect_ratio,
                style_pack_id="stub-style-pack",
            ),
            ImageJob(
                job_id="last-shot-01",
                job_kind="last_frame",
                target_shot_id="shot-01",
                prompt="Generate last frame for shot 01",
                negative_prompt="",
                aspect_ratio=brief.aspect_ratio,
                style_pack_id="stub-style-pack",
            ),
            ImageJob(
                job_id="first-shot-02",
                job_kind="first_frame",
                target_shot_id="shot-02",
                prompt="Generate first frame for shot 02",
                negative_prompt="",
                aspect_ratio=brief.aspect_ratio,
                style_pack_id="stub-style-pack",
            ),
            ImageJob(
                job_id="last-shot-02",
                job_kind="last_frame",
                target_shot_id="shot-02",
                prompt="Generate last frame for shot 02",
                negative_prompt="",
                aspect_ratio=brief.aspect_ratio,
                style_pack_id="stub-style-pack",
            ),
        ]
        storyboard = StoryboardPackage(
            total_duration_seconds=12,
            shots=shots,
            continuity_notes=["Keep the bridge silhouette stable."],
            first_test_shot_ids=["shot-01"],
        )
        return storyboard, frame_jobs

    def review_storyboard(
        self,
        brief: ProjectBrief,
        story: StoryPackage,
        library: AssetLibrary,
        storyboard: StoryboardPackage,
        state: VideoAgentState,
    ) -> AdFeedback:
        return AdFeedback(
            decision=ReviewDecision.APPROVED,
            summary="Storyboard approved in stub mode.",
            high_risk_shot_ids=["shot-02"],
            first_test_shot_ids=storyboard.first_test_shot_ids,
        )


class StubImageProductionAgent:
    """Stub image-production agent."""

    def process_image_job(self, job: ImageJob, library: AssetLibrary) -> ImageJob:
        job.status = "done"
        output_root = Path(library.root_path) / "_generated"
        output_root.mkdir(parents=True, exist_ok=True)
        job.output_image_path = str(output_root / f"{job.job_id}.png")
        return job


class StubVideoProductionAgent:
    """Stub video-production agent."""

    def process_video_job(self, job: VideoJob) -> VideoJob:
        job.status = "done"
        job.output_video_path = f"/tmp/{job.job_id}.mp4"
        return job


def build_stub_services() -> VideoAgentServices:
    """Return a complete stub service bundle."""

    return VideoAgentServices(
        producer=StubProducerAgent(),
        screenwriter=StubScreenwriterAgent(),
        art_design=StubArtDesignAgent(),
        assistant_director=StubAssistantDirectorAgent(),
        image_production=StubImageProductionAgent(),
        video_production=StubVideoProductionAgent(),
    )
