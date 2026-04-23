"""Export Slate runtime JSON Schemas into a single file.

Example:
    >>> from pathlib import Path
    >>> output = Path("runtime/video_agents/schemas.json")
    >>> output.parent.exists()
    True
"""

from __future__ import annotations

import json
from pathlib import Path

from .assets import Asset
from .schemas import (
    AdFeedback,
    ArtGenerationPlan,
    CameraSpec,
    CharacterCard,
    FeedbackItem,
    FrameRef,
    ImageJob,
    ImageRefSlot,
    ModelProfile,
    ProductionPacket,
    ProductionTodoItem,
    ProjectBrief,
    RevisionRequest,
    SceneSpec,
    Segment,
    Shot,
    ShotRenderRequest,
    StoryBeat,
    StoryPackage,
    StoryboardPackage,
    VideoJob,
)


SCHEMA_MODELS = {
    "Asset": Asset,
    "ProjectBrief": ProjectBrief,
    "CharacterCard": CharacterCard,
    "SceneSpec": SceneSpec,
    "StoryBeat": StoryBeat,
    "StoryPackage": StoryPackage,
    "CameraSpec": CameraSpec,
    "FrameRef": FrameRef,
    "Shot": Shot,
    "StoryboardPackage": StoryboardPackage,
    "ImageJob": ImageJob,
    "ArtGenerationPlan": ArtGenerationPlan,
    "ImageRefSlot": ImageRefSlot,
    "ShotRenderRequest": ShotRenderRequest,
    "VideoJob": VideoJob,
    "ModelProfile": ModelProfile,
    "Segment": Segment,
    "RevisionRequest": RevisionRequest,
    "AdFeedback": AdFeedback,
    "FeedbackItem": FeedbackItem,
    "ProductionTodoItem": ProductionTodoItem,
    "ProductionPacket": ProductionPacket,
}


def export_schemas(output_path: Path) -> None:
    """Write all runtime schemas into a single JSON document."""

    payload = {
        "generated_by": "runtime.video_agents.export_schemas",
        "schemas": {
            name: model.model_json_schema()
            for name, model in SCHEMA_MODELS.items()
        },
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """CLI entry point used by `python -m runtime.video_agents.export_schemas`."""

    export_schemas(Path(__file__).with_name("schemas.json"))


if __name__ == "__main__":
    main()
