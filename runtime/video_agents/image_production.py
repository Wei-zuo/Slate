"""Image-production queue node for Slate v0.3."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .assets import AssetLibrary
from .schemas import AdFeedback, FrameRef, ImageJob, ReviewDecision, RevisionRequest, RevisionTarget
from .services import VideoAgentServices
from .state import AuditEntry, VideoAgentState, WorkflowPhase


def _append_log(state: VideoAgentState, event: str, detail: str) -> list[AuditEntry]:
    audit_log = list(state.get("audit_log", []))
    audit_log.append(AuditEntry(phase=WorkflowPhase.IMAGE_PRODUCTION, event=event, detail=detail))
    return audit_log


def _increment_node_runs(state: VideoAgentState) -> dict[str, int]:
    node_runs = dict(state.get("node_runs", {}))
    node_runs["image_production"] = node_runs.get("image_production", 0) + 1
    return node_runs


def _terminalize_image_job(job: ImageJob, library: AssetLibrary, services: VideoAgentServices) -> ImageJob:
    working = deepcopy(job)
    while working.status == "pending":
        working.status = "in_progress"
        result = services.image_production.process_image_job(working, library)
        if result.status == "done":
            return result
        result.retry_count += 1
        if result.retry_count >= 2:
            result.status = "failed"
            return result
        result.status = "pending"
        working = result
    return working


def image_production_node(state: VideoAgentState, services: VideoAgentServices) -> VideoAgentState:
    """Process all currently queued image jobs to terminal status."""

    library = AssetLibrary(Path(state["asset_library_path"]))
    library.load()
    jobs = [deepcopy(job) for job in state.get("pending_image_jobs", [])]
    storyboard = deepcopy(state.get("storyboard"))
    updated_jobs: list[ImageJob] = []
    failed_jobs: list[ImageJob] = []

    for job in jobs:
        if job.status != "pending":
            updated_jobs.append(job)
            continue
        result = _terminalize_image_job(job, library, services)
        if result.status == "done":
            if result.job_kind == "asset_image" and result.target_asset_id and result.output_image_path:
                asset = library.get(result.target_asset_id)
                if asset is not None and result.output_image_path not in asset.reference_image_paths:
                    asset.reference_image_paths.append(result.output_image_path)
                    asset.status = "generated"
            elif storyboard is not None and result.target_shot_id and result.output_image_path:
                target_shot = next((shot for shot in storyboard.shots if shot.shot_id == result.target_shot_id), None)
                if target_shot is not None:
                    if result.job_kind == "first_frame":
                        if target_shot.first_frame_ref is None:
                            target_shot.first_frame_ref = FrameRef(source="to_generate")
                        target_shot.first_frame_ref.image_path = result.output_image_path
                    elif result.job_kind == "last_frame":
                        if target_shot.last_frame_ref is None:
                            target_shot.last_frame_ref = FrameRef(source="to_generate")
                        target_shot.last_frame_ref.image_path = result.output_image_path
        else:
            failed_jobs.append(result)
        updated_jobs.append(result)

    library.save()
    audit_log = _append_log(
        state,
        "image_production_pass_completed",
        f"{sum(job.status == 'done' for job in updated_jobs)} done / {len(failed_jobs)} failed",
    )

    response: VideoAgentState = {
        "pending_image_jobs": updated_jobs,
        "storyboard": storyboard,
        "audit_log": audit_log,
        "node_runs": _increment_node_runs(state),
    }

    if failed_jobs:
        target = RevisionTarget.ART_DESIGN
        decision = ReviewDecision.REVISE_ART
        if any(job.job_kind in {"first_frame", "last_frame"} for job in failed_jobs):
            target = RevisionTarget.ASSISTANT_DIRECTOR
            decision = ReviewDecision.REVISE_STORYBOARD
        blocking_issues = [
            f"Image job {job.job_id} failed after {job.retry_count} attempts: {job.error or 'unknown error'}"
            for job in failed_jobs
        ]
        response["ad_feedback"] = AdFeedback(
            decision=decision,
            summary="Image production failed; route back before the next downstream stage.",
            blocking_issues=blocking_issues,
            revision_request=RevisionRequest(
                target=target,
                reason="image_production_failed",
                blocking_issues=blocking_issues,
                requested_changes=["Fix image-generation blockers and requeue the failed jobs."],
                retry_budget=1,
            ),
        )

    return response
