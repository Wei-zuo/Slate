from __future__ import annotations

from runtime.video_agents.graph import build_video_agent_graph
from runtime.video_agents.model_profile import EXAMPLE_PROFILE
from runtime.video_agents.state import WorkflowPhase
from runtime.video_agents.stubs import build_stub_services


def test_graph_smoke(tmp_path) -> None:
    graph = build_video_agent_graph(build_stub_services())
    result = graph.invoke(
        {
            "phase": WorkflowPhase.PRODUCER_INTAKE,
            "asset_library_path": str(tmp_path / "assets"),
            "model_profile": EXAMPLE_PROFILE,
            "pending_image_jobs": [],
            "pending_video_jobs": [],
        }
    )
    assert result["phase"] == WorkflowPhase.DONE
    assert result["node_runs"]["image_production"] == 2
    assert result["node_runs"]["video_production"] == 1
