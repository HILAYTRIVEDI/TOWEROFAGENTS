from typing import Any

from workflows.graph import WorkflowState


class WorkflowExecutor:
    async def run(self, state: WorkflowState) -> dict[str, Any]:
        raise NotImplementedError("Workflow execution is not implemented in the bootstrap")

