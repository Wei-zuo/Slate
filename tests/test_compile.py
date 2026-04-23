from __future__ import annotations

from pathlib import Path

from runtime.video_agents.assets import Asset, AssetLibrary
from runtime.video_agents.compile import _resolve_mentions, compile_shot
from runtime.video_agents.model_profile import EXAMPLE_PROFILE
from runtime.video_agents.schemas import CameraSpec, ProjectBrief, Shot


def test_compile_shot_handles_coref_and_negative_fragments(tmp_path: Path) -> None:
    root = tmp_path / "assets"
    library = AssetLibrary(root)
    library.add(
        Asset(
            asset_id="zhangguolao",
            asset_type="character",
            name="张果老",
            aliases=["张果佬"],
            description="倒骑白驴的老仙人",
            visual_hooks=["倒骑白驴", "斗笠"],
            reference_image_paths=["character/zhangguolao.png"],
            status="approved",
            created_by_phase="art_design",
            created_by_agent="image_production",
            notes="",
        )
    )
    library.add(
        Asset(
            asset_id="luban",
            asset_type="character",
            name="鲁班",
            aliases=[],
            description="壮年匠人",
            visual_hooks=["石锤"],
            reference_image_paths=["character/luban.png"],
            status="approved",
            created_by_phase="art_design",
            created_by_agent="image_production",
            notes="",
        )
    )
    library.add(
        Asset(
            asset_id="style-pack",
            asset_type="style_pack",
            name="2D 国风风格包",
            aliases=["国风风格"],
            description="2D hand-drawn guofeng",
            visual_hooks=["青灰石色"],
            reference_image_paths=[],
            status="approved",
            created_by_phase="art_design",
            created_by_agent="art_design",
            notes="",
        )
    )
    library.save()

    brief = ProjectBrief(
        project_id="demo",
        route="adaptation",
        title="demo",
        goal="demo",
        platform="OpenClaw",
        format="2D short",
        target_duration_seconds=12,
        language="zh-CN",
        aspect_ratio="16:9",
        delivery_scope="shot render requests",
    )
    shot = Shot(
        shot_id="shot-01",
        beat_id="beat-01",
        duration_seconds=5,
        description="镜头先对准张果老，再切到他皱眉。鲁班在背景里没有说话。",
        involved_asset_ids=["luban", "zhangguolao"],
        camera=CameraSpec(movement="缓推", shot_size="medium", position="front"),
        style_pack_id="style-pack",
        risk_level="medium",
        notes="",
    )

    mentions = _resolve_mentions(shot, library)
    assert [mention.asset.asset_id for mention in mentions if mention.kind == "coref"] == ["zhangguolao"]

    request = compile_shot(shot, library, EXAMPLE_PROFILE, brief)
    assert request.ref_images[0].asset_id == "zhangguolao"
    assert "no subtitles" in request.negative_text
    assert request.aspect_ratio == "16:9"
