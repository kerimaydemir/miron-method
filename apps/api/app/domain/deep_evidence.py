import json
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from app.domain.fixtures import CanonicalFixture


class EvidenceArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    endpoint: str
    observed_at: datetime
    records: tuple[dict[str, Any], ...] = ()


class DeepFootballEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    provider_fixture_id: str
    observed_at: datetime
    home_team_id: int
    away_team_id: int
    league_id: int
    season: int
    artifacts: tuple[EvidenceArtifact, ...]
    coverage: dict[str, bool]

    def compact_packet(self, *, records_per_artifact: int = 30) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_fixture_id": self.provider_fixture_id,
            "observed_at": self.observed_at.isoformat(),
            "coverage": self.coverage,
            "artifacts": [
                {
                    "kind": artifact.kind,
                    "endpoint": artifact.endpoint,
                    "observed_at": artifact.observed_at.isoformat(),
                    "record_count": len(artifact.records),
                    "records": [
                        self._bounded_record(record)
                        for record in artifact.records[:records_per_artifact]
                    ],
                }
                for artifact in self.artifacts
            ],
        }

    @staticmethod
    def _bounded_record(record: dict[str, Any]) -> dict[str, Any]:
        serialized = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        if len(serialized) <= 20_000:
            return record
        return {
            "truncated": True,
            "json_prefix": serialized[:20_000],
            "original_characters": len(serialized),
        }


class DeepEvidenceProvider(Protocol):
    @property
    def available(self) -> bool: ...

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence: ...
