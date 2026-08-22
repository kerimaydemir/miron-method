from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

STAGE_IDS = tuple(f"S{index:02d}" for index in range(31))


@dataclass(frozen=True)
class AnalysisWorkflowInput:
    run_id: str
    fixture_id: str
    cutoff_at: str


@dataclass(frozen=True)
class StageActivityInput:
    run_id: str
    fixture_id: str
    cutoff_at: str
    stage_id: str


@dataclass(frozen=True)
class StageActivityResult:
    stage_id: str
    status: str
    completed_at: str


@dataclass(frozen=True)
class AnalysisWorkflowResult:
    run_id: str
    state: str
    completed_stage_ids: tuple[str, ...]


@activity.defn
async def execute_analysis_stage(stage: StageActivityInput) -> StageActivityResult:
    """Execute one idempotent stage boundary.

    Provider and persistence adapters will replace the deterministic pilot body;
    keeping an activity boundary now gives retries, histories, and cancellation.
    """

    activity.logger.info(
        "analysis stage completed",
        extra={"run_id": stage.run_id, "stage_id": stage.stage_id},
    )
    return StageActivityResult(
        stage_id=stage.stage_id,
        status="COMPLETED",
        completed_at=datetime.now(UTC).isoformat(),
    )


@workflow.defn(name="pre-match-analysis.v1")
class PreMatchAnalysisWorkflow:
    @workflow.run
    async def run(self, request: AnalysisWorkflowInput) -> AnalysisWorkflowResult:
        completed: list[str] = []
        for stage_id in STAGE_IDS:
            result = await workflow.execute_activity(
                execute_analysis_stage,
                StageActivityInput(
                    run_id=request.run_id,
                    fixture_id=request.fixture_id,
                    cutoff_at=request.cutoff_at,
                    stage_id=stage_id,
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(milliseconds=250),
                    maximum_interval=timedelta(seconds=5),
                    maximum_attempts=3,
                ),
            )
            completed.append(result.stage_id)
        return AnalysisWorkflowResult(
            run_id=request.run_id,
            state="LOCKING",
            completed_stage_ids=tuple(completed),
        )
