"""Video-production queue node for Slate v0.3."""

from __future__ import annotations

from copy import deepcopy

from .schemas import VideoJob
from .services import VideoAgentServices
from .state import AuditEntry, VideoAgentState, WorkflowPhase


def _append_log(state: VideoAgentState, event: str, detail: str) -> list[AuditEntry]:
    audit_log = list(state.get("audit_log", []))
    audit_log.append(AuditEntry(phase=WorkflowPhase.VIDEO_PRODUCTION, event=event, detail=detail))
    return audit_log


def _increment_node_runs(state: VideoAgentState) -> dict[str, int]:
    node_runs = dict(state.get("node_runs", {}))
    node_runs["video_production"] = node_runs.get("video_production", 0) + 1
    return node_runs


def _terminalize_video_job(job: VideoJob, services: VideoAgentServices) -> VideoJob:
    working = deepcopy(job)
    while working.status == "pending":
        working.status = "in_progress"
        result = services.video_production.process_video_job(working)
        if result.status == "done":
            return result
        result.retry_count += 1
        if result.retry_count > 1:
            result.status = "failed"
            return result
        result.status = "pending"
        working = result
    return working


def video_production_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    """Process all pending video jobs."""

    jobs = [deepcopy(job) for job in state.get("pending_video_jobs", [])]
    updated_jobs: list[VideoJob] = []
    failed_jobs: list[VideoJob] = []
    for job in jobs:
        if job.status != "pending":
            updated_jobs.append(job)
            continue
        result = _terminalize_video_job(job, services)
        if result.status == "failed":
            failed_jobs.append(result)
        updated_jobs.append(result)

    phase = WorkflowPhase.FAILED if failed_jobs else WorkflowPhase.DONE
    detail = f"{sum(job.status == 'done' for job in updated_jobs)} done / {len(failed_jobs)} failed"
    return {
        "phase": phase,
        "pending_video_jobs": updated_jobs,
        "stop_reason": "Video production failed." if failed_jobs else None,
        "audit_log": _append_log(state, "video_production_pass_completed", detail),
        "node_runs": _increment_node_runs(state),
    }
