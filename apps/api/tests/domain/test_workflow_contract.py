from app.workflows.analysis import STAGE_IDS


def test_pre_match_workflow_registers_exactly_31_ordered_stages() -> None:
    assert tuple(f"S{index:02d}" for index in range(31)) == STAGE_IDS
