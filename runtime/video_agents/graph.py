from __future__ import annotations

from copy import deepcopy

from langgraph.graph import END, START, StateGraph

from .schemas import ReviewDecision, RevisionTarget
from .services import VideoAgentServices
from .state import AuditEntry, RevisionCounter, RevisionLimits, VideoAgentState, WorkflowPhase


def _append_log(state: VideoAgentState, phase: WorkflowPhase, event: str, detail: str) -> list[AuditEntry]:
    audit_log = list(state.get("audit_log", []))
    audit_log.append(AuditEntry(phase=phase, event=event, detail=detail))
    return audit_log


def _revision_counts(state: VideoAgentState) -> RevisionCounter:
    return deepcopy(state.get("revision_counts", RevisionCounter()))


def _revision_limits(state: VideoAgentState) -> RevisionLimits:
    return deepcopy(state.get("revision_limits", RevisionLimits()))


def _producer_intake_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    brief = state.get("brief") or services.normalize_brief(state)
    return {
        "phase": WorkflowPhase.SCREENWRITER,
        "brief": brief,
        "revision_counts": _revision_counts(state),
        "revision_limits": _revision_limits(state),
        "audit_log": _append_log(state, WorkflowPhase.PRODUCER_INTAKE, "brief_frozen", brief.title),
    }


def _screenwriter_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    story = services.write_story_package(state["brief"], state)
    return {
        "phase": WorkflowPhase.ART_DESIGN,
        "story_package": story,
        "active_revision": None,
        "audit_log": _append_log(state, WorkflowPhase.SCREENWRITER, "story_package_written", story.title),
    }


def _art_design_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    art = services.write_art_package(state["brief"], state["story_package"], state)
    return {
        "phase": WorkflowPhase.ASSISTANT_DIRECTOR,
        "art_package": art,
        "active_revision": None,
        "audit_log": _append_log(state, WorkflowPhase.ART_DESIGN, "art_package_written", art.style_name),
    }


def _assistant_director_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    result = services.review_storyboard(
        state["brief"],
        state["story_package"],
        state["art_package"],
        state,
    )
    return {
        "storyboard": result.storyboard,
        "ad_feedback": result.feedback,
        "audit_log": _append_log(
            state,
            WorkflowPhase.ASSISTANT_DIRECTOR,
            "storyboard_reviewed",
            result.feedback.decision,
        ),
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
        stop_reason = "Revision requested without revision payload."
    elif active_revision.target == RevisionTarget.SCREENWRITER:
        counts.screenwriter += 1
        next_phase = WorkflowPhase.SCREENWRITER
    elif active_revision.target == RevisionTarget.ART_DESIGN:
        counts.art_design += 1
        next_phase = WorkflowPhase.ART_DESIGN
    else:
        counts.assistant_director += 1
        next_phase = WorkflowPhase.ASSISTANT_DIRECTOR

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
        "active_revision": active_revision if next_phase in {WorkflowPhase.SCREENWRITER, WorkflowPhase.ART_DESIGN, WorkflowPhase.ASSISTANT_DIRECTOR} else None,
        "stop_reason": stop_reason,
        "audit_log": _append_log(state, WorkflowPhase.ASSISTANT_DIRECTOR, "revision_routed", detail),
    }


def _producer_integration_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    packet = services.integrate_packet(
        state["brief"],
        state["story_package"],
        state["art_package"],
        state["storyboard"],
        state,
    )
    next_phase = WorkflowPhase.PRODUCTION if state.get("should_run_production") else WorkflowPhase.DONE
    return {
        "phase": next_phase,
        "production_packet": packet,
        "audit_log": _append_log(state, WorkflowPhase.PRODUCER_INTEGRATION, "production_packet_compiled", packet.brief.project_id),
    }


def _production_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    services.run_production(state["production_packet"], state)
    return {
        "phase": WorkflowPhase.DONE,
        "audit_log": _append_log(state, WorkflowPhase.PRODUCTION, "production_completed", state["production_packet"].brief.project_id),
    }


def _failed_node(state: VideoAgentState) -> VideoAgentState:
    detail = state.get("stop_reason", "Workflow failed without explicit stop reason.")
    return {
        "phase": WorkflowPhase.FAILED,
        "audit_log": _append_log(state, WorkflowPhase.FAILED, "workflow_failed", detail),
    }


def _route_after_revision(state: VideoAgentState) -> str:
    phase = state["phase"]
    if phase == WorkflowPhase.SCREENWRITER:
        return "screenwriter"
    if phase == WorkflowPhase.ART_DESIGN:
        return "art_design"
    if phase == WorkflowPhase.ASSISTANT_DIRECTOR:
        return "assistant_director"
    if phase == WorkflowPhase.PRODUCER_INTEGRATION:
        return "producer_integration"
    return "failed"


def _route_after_integration(state: VideoAgentState) -> str:
    if state["phase"] == WorkflowPhase.PRODUCTION:
        return "production"
    return "done"


def build_video_agent_graph(services: VideoAgentServices):
    builder = StateGraph(VideoAgentState)

    builder.add_node("producer_intake", lambda state: _producer_intake_node(state, services))
    builder.add_node("screenwriter", lambda state: _screenwriter_node(state, services))
    builder.add_node("art_design", lambda state: _art_design_node(state, services))
    builder.add_node("assistant_director", lambda state: _assistant_director_node(state, services))
    builder.add_node("revision_router", _revision_router_node)
    builder.add_node("producer_integration", lambda state: _producer_integration_node(state, services))
    builder.add_node("production", lambda state: _production_node(state, services))
    builder.add_node("failed", _failed_node)

    builder.add_edge(START, "producer_intake")
    builder.add_edge("producer_intake", "screenwriter")
    builder.add_edge("screenwriter", "art_design")
    builder.add_edge("art_design", "assistant_director")
    builder.add_edge("assistant_director", "revision_router")

    builder.add_conditional_edges(
        "revision_router",
        _route_after_revision,
        {
            "screenwriter": "screenwriter",
            "art_design": "art_design",
            "assistant_director": "assistant_director",
            "producer_integration": "producer_integration",
            "failed": "failed",
        },
    )

    builder.add_conditional_edges(
        "producer_integration",
        _route_after_integration,
        {
            "production": "production",
            "done": END,
        },
    )

    builder.add_edge("production", END)
    builder.add_edge("failed", END)

    return builder.compile()
