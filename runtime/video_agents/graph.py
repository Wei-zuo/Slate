"""LangGraph orchestration for the Slate v0.3 runtime.

The graph matches the README flow:

producer_intake -> screenwriter -> art_design -> image_production
-> assistant_director_cut -> image_production -> assistant_director_review
-> revision_router -> producer_integration -> video_production
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from .assets import AssetLibrary
from .compile import compile_all_shots
from .image_production import image_production_node
from .model_profile import EXAMPLE_PROFILE
from .schemas import (
    AdFeedback,
    ProductionPacket,
    ReviewDecision,
    RevisionRequest,
    RevisionTarget,
    ShotRenderRequest,
    VideoJob,
)
from .segment import pack_segments
from .services import VideoAgentServices
from .state import AuditEntry, RevisionCounter, RevisionLimits, VideoAgentState, WorkflowPhase
from .video_production import video_production_node


def _append_log(state: VideoAgentState, phase: WorkflowPhase, event: str, detail: str) -> list[AuditEntry]:
    audit_log = list(state.get("audit_log", []))
    audit_log.append(AuditEntry(phase=phase, event=event, detail=detail))
    return audit_log


def _increment_node_runs(state: VideoAgentState, node_name: str) -> dict[str, int]:
    node_runs = dict(state.get("node_runs", {}))
    node_runs[node_name] = node_runs.get(node_name, 0) + 1
    return node_runs


def _revision_counts(state: VideoAgentState) -> RevisionCounter:
    return deepcopy(state.get("revision_counts", RevisionCounter()))


def _revision_limits(state: VideoAgentState) -> RevisionLimits:
    return deepcopy(state.get("revision_limits", RevisionLimits()))


def _load_library(state: VideoAgentState) -> AssetLibrary:
    library = AssetLibrary(Path(state["asset_library_path"]))
    library.load()
    return library


def _producer_intake_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    brief = state.get("brief") or services.producer.normalize_brief(state)
    return {
        "phase": WorkflowPhase.SCREENWRITER,
        "brief": brief,
        "revision_counts": _revision_counts(state),
        "revision_limits": _revision_limits(state),
        "pending_image_jobs": list(state.get("pending_image_jobs", [])),
        "pending_video_jobs": list(state.get("pending_video_jobs", [])),
        "audit_log": _append_log(state, WorkflowPhase.PRODUCER_INTAKE, "brief_frozen", brief.title),
        "node_runs": _increment_node_runs(state, "producer_intake"),
    }


def _screenwriter_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    story = services.screenwriter.write_story_package(state["brief"], state)
    library = _load_library(state)
    for asset in services.producer.bootstrap_stub_assets(state["brief"], story, library):
        library.add(asset)
    library.save()
    return {
        "phase": WorkflowPhase.ART_DESIGN,
        "story_package": story,
        "active_revision": None,
        "audit_log": _append_log(state, WorkflowPhase.SCREENWRITER, "story_package_written", story.title),
        "node_runs": _increment_node_runs(state, "screenwriter"),
    }


def _art_design_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    library = _load_library(state)
    plan = services.art_design.plan_art_generation(state["brief"], state["story_package"], library, state)
    return {
        "phase": WorkflowPhase.ASSISTANT_DIRECTOR_CUT,
        "art_generation_plan": plan,
        "pending_image_jobs": plan.asset_jobs,
        "active_revision": None,
        "audit_log": _append_log(
            state,
            WorkflowPhase.ART_DESIGN,
            "art_generation_planned",
            f"{len(plan.asset_jobs)} image jobs queued",
        ),
        "node_runs": _increment_node_runs(state, "art_design"),
    }


def _assistant_director_cut_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    pending = [job for job in state.get("pending_image_jobs", []) if job.status in {"pending", "in_progress"}]
    if pending:
        raise RuntimeError("pending_image_jobs must be empty before assistant_director_cut.")
    library = _load_library(state)
    storyboard, frame_jobs = services.assistant_director.cut_storyboard(
        state["brief"],
        state["story_package"],
        library,
        state,
    )
    return {
        "phase": WorkflowPhase.ASSISTANT_DIRECTOR_REVIEW,
        "storyboard": storyboard,
        "pending_image_jobs": frame_jobs,
        "audit_log": _append_log(
            state,
            WorkflowPhase.ASSISTANT_DIRECTOR_CUT,
            "storyboard_cut",
            f"{len(storyboard.shots)} shots / {len(frame_jobs)} frame jobs",
        ),
        "node_runs": _increment_node_runs(state, "assistant_director_cut"),
    }


def _assistant_director_review_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    pending = [job for job in state.get("pending_image_jobs", []) if job.status in {"pending", "in_progress"}]
    if pending:
        raise RuntimeError("pending_image_jobs must be empty before assistant_director_review.")
    library = _load_library(state)
    feedback = services.assistant_director.review_storyboard(
        state["brief"],
        state["story_package"],
        library,
        state["storyboard"],
        state,
    )
    if feedback.decision == ReviewDecision.APPROVED:
        for asset in library.assets.values():
            if asset.status == "generated":
                asset.status = "approved"
        library.save()
    return {
        "ad_feedback": feedback,
        "audit_log": _append_log(
            state,
            WorkflowPhase.ASSISTANT_DIRECTOR_REVIEW,
            "storyboard_reviewed",
            feedback.decision,
        ),
        "node_runs": _increment_node_runs(state, "assistant_director_review"),
    }


def _revision_router_node(state: VideoAgentState) -> VideoAgentState:
    feedback = state["ad_feedback"]
    counts = _revision_counts(state)
    limits = _revision_limits(state)
    active_revision = feedback.revision_request
    stop_reason = None

    if feedback.decision == ReviewDecision.APPROVED:
        next_phase = WorkflowPhase.PRODUCER_INTEGRATION
    elif feedback.decision == ReviewDecision.BLOCKED:
        next_phase = WorkflowPhase.FAILED
        stop_reason = feedback.summary
    elif active_revision is None:
        next_phase = WorkflowPhase.FAILED
        stop_reason = "Revision requested without a revision payload."
    elif active_revision.target == RevisionTarget.SCREENWRITER:
        counts.screenwriter += 1
        next_phase = WorkflowPhase.SCREENWRITER
    elif active_revision.target == RevisionTarget.ART_DESIGN:
        counts.art_design += 1
        next_phase = WorkflowPhase.ART_DESIGN
    else:
        counts.assistant_director += 1
        next_phase = WorkflowPhase.ASSISTANT_DIRECTOR_CUT

    if counts.screenwriter > limits.screenwriter:
        next_phase = WorkflowPhase.FAILED
        stop_reason = "Exceeded screenwriter revision budget."
    elif counts.art_design > limits.art_design:
        next_phase = WorkflowPhase.FAILED
        stop_reason = "Exceeded art-design revision budget."
    elif counts.assistant_director > limits.assistant_director:
        next_phase = WorkflowPhase.FAILED
        stop_reason = "Exceeded assistant-director revision budget."
    elif counts.total() > limits.total:
        next_phase = WorkflowPhase.FAILED
        stop_reason = "Exceeded total revision budget."

    detail = stop_reason or feedback.decision
    return {
        "phase": next_phase,
        "revision_counts": counts,
        "active_revision": active_revision if next_phase in {WorkflowPhase.SCREENWRITER, WorkflowPhase.ART_DESIGN, WorkflowPhase.ASSISTANT_DIRECTOR_CUT} else None,
        "stop_reason": stop_reason,
        "audit_log": _append_log(state, WorkflowPhase.ASSISTANT_DIRECTOR_REVIEW, "revision_routed", detail),
        "node_runs": _increment_node_runs(state, "revision_router"),
    }


def _producer_integration_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    if not state.get("storyboard") or not state.get("art_generation_plan"):
        raise RuntimeError("production_packet must not be compiled before storyboard and art generation plan exist.")

    library = _load_library(state)
    model_profile = state.get("model_profile", EXAMPLE_PROFILE)
    render_requests = compile_all_shots(state["storyboard"], library, model_profile, state["brief"])
    video_jobs = [
        VideoJob(
            job_id=f"video-{request.shot_id}",
            shot_id=request.shot_id,
            render_request=request,
        )
        for request in render_requests
    ]
    segments = pack_segments(
        scenes=state["story_package"].scenes,
        beats=state["story_package"].beats,
        shots=state["storyboard"].shots,
        max_segment_seconds=model_profile.max_seconds,
    )
    integration_state = dict(state)
    integration_state["pending_video_jobs"] = video_jobs
    packet = services.producer.integrate_packet(
        state["brief"],
        state["story_package"],
        state["art_generation_plan"],
        state["storyboard"],
        integration_state,
    )
    if not isinstance(packet, ProductionPacket):
        raise TypeError("Producer integration must return ProductionPacket.")
    packet.render_requests = list(render_requests)
    packet.segments = list(segments)

    return {
        "phase": WorkflowPhase.VIDEO_PRODUCTION,
        "production_packet": packet,
        "pending_video_jobs": video_jobs,
        "audit_log": _append_log(
            state,
            WorkflowPhase.PRODUCER_INTEGRATION,
            "production_packet_compiled",
            f"{len(render_requests)} shot render requests",
        ),
        "node_runs": _increment_node_runs(state, "producer_integration"),
    }


def _fail_closed_node(state: VideoAgentState) -> VideoAgentState:
    detail = state.get("stop_reason", "Workflow failed without explicit stop reason.")
    return {
        "phase": WorkflowPhase.FAILED,
        "audit_log": _append_log(state, WorkflowPhase.FAILED, "workflow_failed", detail),
        "node_runs": _increment_node_runs(state, "fail_closed"),
    }


def _route_after_art_design(state: VideoAgentState) -> str:
    if state.get("pending_image_jobs"):
        return "image_production"
    return "assistant_director_cut"


def _route_after_image_production(state: VideoAgentState) -> str:
    jobs = state.get("pending_image_jobs", [])
    if any(job.status == "failed" for job in jobs):
        return "revision_router"
    phase = state.get("phase")
    if phase == WorkflowPhase.ASSISTANT_DIRECTOR_CUT:
        return "assistant_director_cut"
    if phase == WorkflowPhase.ASSISTANT_DIRECTOR_REVIEW:
        return "assistant_director_review"
    return "fail_closed"


def _route_after_cut(state: VideoAgentState) -> str:
    if state.get("pending_image_jobs"):
        return "image_production"
    return "assistant_director_review"


def _route_after_revision(state: VideoAgentState) -> str:
    phase = state["phase"]
    if phase == WorkflowPhase.SCREENWRITER:
        return "screenwriter"
    if phase == WorkflowPhase.ART_DESIGN:
        return "art_design"
    if phase == WorkflowPhase.ASSISTANT_DIRECTOR_CUT:
        return "assistant_director_cut"
    if phase == WorkflowPhase.PRODUCER_INTEGRATION:
        return "producer_integration"
    return "fail_closed"


def _route_after_video(state: VideoAgentState) -> str:
    if state.get("phase") == WorkflowPhase.DONE:
        return "done"
    return "fail_closed"


def build_video_agent_graph(services: VideoAgentServices):
    """Build the Slate v0.3 LangGraph workflow."""

    builder = StateGraph(VideoAgentState)

    builder.add_node("producer_intake", lambda state: _producer_intake_node(state, services))
    builder.add_node("screenwriter", lambda state: _screenwriter_node(state, services))
    builder.add_node("art_design", lambda state: _art_design_node(state, services))
    builder.add_node("image_production", lambda state: image_production_node(state, services))
    builder.add_node("assistant_director_cut", lambda state: _assistant_director_cut_node(state, services))
    builder.add_node("assistant_director_review", lambda state: _assistant_director_review_node(state, services))
    builder.add_node("revision_router", _revision_router_node)
    builder.add_node("producer_integration", lambda state: _producer_integration_node(state, services))
    builder.add_node("video_production", lambda state: video_production_node(state, services))
    builder.add_node("fail_closed", _fail_closed_node)

    builder.add_edge(START, "producer_intake")
    builder.add_edge("producer_intake", "screenwriter")
    builder.add_edge("screenwriter", "art_design")

    builder.add_conditional_edges(
        "art_design",
        _route_after_art_design,
        {
            "image_production": "image_production",
            "assistant_director_cut": "assistant_director_cut",
        },
    )

    builder.add_conditional_edges(
        "image_production",
        _route_after_image_production,
        {
            "assistant_director_cut": "assistant_director_cut",
            "assistant_director_review": "assistant_director_review",
            "revision_router": "revision_router",
            "fail_closed": "fail_closed",
        },
    )

    builder.add_conditional_edges(
        "assistant_director_cut",
        _route_after_cut,
        {
            "image_production": "image_production",
            "assistant_director_review": "assistant_director_review",
        },
    )

    builder.add_edge("assistant_director_review", "revision_router")

    builder.add_conditional_edges(
        "revision_router",
        _route_after_revision,
        {
            "screenwriter": "screenwriter",
            "art_design": "art_design",
            "assistant_director_cut": "assistant_director_cut",
            "producer_integration": "producer_integration",
            "fail_closed": "fail_closed",
        },
    )

    builder.add_edge("producer_integration", "video_production")

    builder.add_conditional_edges(
        "video_production",
        _route_after_video,
        {
            "done": END,
            "fail_closed": "fail_closed",
        },
    )

    builder.add_edge("fail_closed", END)

    return builder.compile()
