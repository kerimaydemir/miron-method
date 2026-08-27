import asyncio
import unicodedata
from datetime import UTC, datetime
from typing import Any

import httpx

from app.domain.deep_evidence import DeepFootballEvidence, EvidenceArtifact
from app.domain.fixtures import CanonicalFixture

EspnParam = str | int | float | bool | None


class EspnSoccerProvider:
    """No-key ESPN public site API evidence adapter.

    ESPN's public JSON site endpoints are useful for match summaries, team
    rosters, injury notes, schedules, and league news. They are intentionally
    treated as fail-soft enrichment: never as odds truth and never as a reason
    to fabricate a coupon when market data is missing.
    """

    source_name = "espn_public_soccer"

    def __init__(
        self,
        *,
        base_url: str = "https://site.api.espn.com/apis/site/v2/sports/soccer",
        core_base_url: str = "https://sports.core.api.espn.com/v2/sports/soccer",
        league_paths: tuple[str, ...] = (
            "eng.1",
            "esp.1",
            "ita.1",
            "ger.1",
            "fra.1",
            "ned.1",
            "por.1",
            "tur.1",
            "uefa.champions",
        ),
        client: httpx.AsyncClient | None = None,
        request_interval_seconds: float = 0.2,
    ) -> None:
        self._league_paths = tuple(path.strip().strip("/") for path in league_paths if path.strip())
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(20.0, connect=5.0),
            headers={"User-Agent": "MIRON-BABA-AI/0.1 espn-public-soccer-evidence"},
        )
        self._core_base_url = core_base_url.rstrip("/")
        self._owns_client = client is None
        self._request_lock = asyncio.Lock()
        self._next_request_at = 0.0
        self._request_interval = 0.0 if client is not None else request_interval_seconds

    @property
    def available(self) -> bool:
        return bool(self._league_paths)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        if not self.available:
            raise PermissionError("ESPN_SOCCER_LEAGUES_REQUIRED")

        observed_at = datetime.now(UTC)
        artifacts: list[EvidenceArtifact] = []
        scanned_events: list[dict[str, Any]] = []
        matched_event: dict[str, Any] = {}
        matched_league = ""

        fixture_date = fixture.kickoff_at.astimezone(UTC).strftime("%Y%m%d")
        for league in self._candidate_leagues(fixture.competition_key):
            try:
                events, endpoint = await self._scoreboard_events(league, fixture_date)
            except Exception:
                continue
            scanned_events.extend(events)
            artifacts.append(
                EvidenceArtifact(
                    kind=f"scoreboard_scan:{league}",
                    endpoint=endpoint,
                    observed_at=observed_at,
                    records=events,
                )
            )
            matched_event = self._match_event(fixture, events)
            if matched_event:
                matched_league = league
                break

        if not matched_event:
            if not artifacts:
                raise KeyError("ESPN_FIXTURE_NOT_FOUND")
            return self._unmatched_evidence(
                fixture=fixture,
                observed_at=observed_at,
                artifacts=artifacts,
                scanned_events=scanned_events,
            )

        event_id = str(matched_event.get("id") or fixture.provider_fixture_id or fixture.id)
        home_team, away_team = self._competitor_teams(matched_event)
        home_team_id = self._int_value(home_team.get("id"))
        away_team_id = self._int_value(away_team.get("id"))
        league_id = self._int_value(self._nested(matched_event, "competitions", 0, "league", "id"))

        artifacts.append(
            EvidenceArtifact(
                kind="scoreboard_match",
                endpoint=f"/{matched_league}/scoreboard",
                observed_at=observed_at,
                records=(matched_event,),
            )
        )

        await self._append_match_artifacts(
            artifacts=artifacts,
            observed_at=observed_at,
            league=matched_league,
            event_id=event_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            fixture=fixture,
            matched_event=matched_event,
        )

        coverage = {artifact.kind: bool(artifact.records) for artifact in artifacts}
        coverage.update(
            {
                "fixture": True,
                "scoreboard": True,
                "summary": any(artifact.kind == "event_summary" and artifact.records for artifact in artifacts),
                "news": any("news" in artifact.kind and artifact.records for artifact in artifacts),
                "rosters": any("roster" in artifact.kind and artifact.records for artifact in artifacts),
                "injuries": any("injuries" in artifact.kind and artifact.records for artifact in artifacts),
                "team_schedules": any("schedule" in artifact.kind and artifact.records for artifact in artifacts),
                "records": any("record" in artifact.kind and artifact.records for artifact in artifacts),
                "odds_context": self._has_odds_context(artifacts),
            }
        )
        return DeepFootballEvidence(
            provider=self.source_name,
            provider_fixture_id=event_id,
            observed_at=observed_at,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            league_id=league_id,
            season=fixture.kickoff_at.year,
            artifacts=tuple(artifacts),
            coverage=coverage,
        )

    async def _append_match_artifacts(
        self,
        *,
        artifacts: list[EvidenceArtifact],
        observed_at: datetime,
        league: str,
        event_id: str,
        home_team_id: int,
        away_team_id: int,
        fixture: CanonicalFixture,
        matched_event: dict[str, Any],
    ) -> None:
        requests: list[tuple[str, str, dict[str, EspnParam]]] = [
            ("event_summary", f"/{league}/summary", {"event": event_id}),
            ("league_news", f"/{league}/news", {}),
        ]
        for side, team_id in (("home", home_team_id), ("away", away_team_id)):
            if team_id:
                requests.extend(
                    (
                        (f"{side}_roster", f"/{league}/teams/{team_id}/roster", {}),
                        (f"{side}_injuries", f"/{league}/teams/{team_id}/injuries", {}),
                        (f"{side}_schedule", f"/{league}/teams/{team_id}/schedule", {}),
                    )
                )

        results = await asyncio.gather(
            *(self._fetch(endpoint, params) for _, endpoint, params in requests),
            return_exceptions=True,
        )
        for (kind, endpoint, _), result in zip(requests, results, strict=True):
            records: tuple[dict[str, Any], ...]
            if isinstance(result, BaseException):
                records = ()
            elif kind == "league_news":
                records = self._news_records(result, fixture)
            elif kind.endswith("_roster"):
                records = self._list_records(result, "athletes")
            elif kind.endswith("_injuries"):
                records = self._list_records(result, "injuries")
            elif kind.endswith("_schedule"):
                records = self._list_records(result, "events")
            else:
                summary_record = self._summary_record(result)
                records = (summary_record,) if summary_record else ()
            artifacts.append(
                EvidenceArtifact(
                    kind=kind,
                    endpoint=endpoint,
                    observed_at=observed_at,
                    records=records,
                )
            )
        await self._append_core_ref_artifacts(
            artifacts=artifacts,
            observed_at=observed_at,
            matched_event=matched_event,
        )

    async def _append_core_ref_artifacts(
        self,
        *,
        artifacts: list[EvidenceArtifact],
        observed_at: datetime,
        matched_event: dict[str, Any] | None,
    ) -> None:
        if not matched_event:
            return
        competition = self._nested(matched_event, "competitions", 0)
        if not isinstance(competition, dict):
            return

        refs: list[tuple[str, str]] = []
        for kind, key in (
            ("core_status", "status"),
            ("core_venue", "venue"),
            ("core_odds", "odds"),
            ("core_broadcasts", "broadcasts"),
            ("core_situation", "situation"),
        ):
            ref = self._ref_value(competition.get(key))
            if ref:
                refs.append((kind, ref))

        competitors = competition.get("competitors")
        if isinstance(competitors, list):
            for competitor in competitors:
                if not isinstance(competitor, dict):
                    continue
                side = "home" if competitor.get("homeAway") == "home" else "away"
                for kind, key in (("record", "record"), ("score", "score")):
                    ref = self._ref_value(competitor.get(key))
                    if ref:
                        refs.append((f"core_{side}_{kind}", ref))

        if not refs:
            return
        results = await asyncio.gather(
            *(self._fetch_absolute(ref, {}) for _, ref in refs[:12]),
            return_exceptions=True,
        )
        for (kind, ref), result in zip(refs[:12], results, strict=True):
            records = () if isinstance(result, BaseException) else (result,)
            artifacts.append(
                EvidenceArtifact(
                    kind=kind,
                    endpoint=ref,
                    observed_at=observed_at,
                    records=records,
                )
            )

    async def _scoreboard_events(
        self, league: str, fixture_date: str
    ) -> tuple[tuple[dict[str, Any], ...], str]:
        try:
            scoreboard = await self._fetch(f"/{league}/scoreboard", {"dates": fixture_date})
            events = tuple(
                event for event in scoreboard.get("events", []) if isinstance(event, dict)
            )
            return events, f"/{league}/scoreboard"
        except Exception:
            events = await self._core_events_for_date(league, fixture_date)
            return events, f"{self._core_base_url}/leagues/{league}/events"

    async def _core_events_for_date(
        self, league: str, fixture_date: str
    ) -> tuple[dict[str, Any], ...]:
        payload = await self._fetch_absolute(
            f"{self._core_base_url}/leagues/{league}/events",
            {"dates": fixture_date, "lang": "en", "region": "us"},
        )
        items = payload.get("items")
        if not isinstance(items, list):
            return ()
        event_refs = tuple(
            self._https_url(str(item.get("$ref")))
            for item in items
            if isinstance(item, dict) and item.get("$ref")
        )
        results = await asyncio.gather(
            *(self._fetch_absolute(ref, {}) for ref in event_refs[:50]),
            return_exceptions=True,
        )
        events: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, dict):
                events.append(await self._hydrate_core_event(result))
        return tuple(events)

    async def _hydrate_core_event(self, event: dict[str, Any]) -> dict[str, Any]:
        competitions = event.get("competitions")
        if not isinstance(competitions, list):
            return event
        for competition in competitions:
            if not isinstance(competition, dict):
                continue
            competitors = competition.get("competitors")
            if not isinstance(competitors, list):
                continue
            team_refs: list[str] = []
            for competitor in competitors:
                if not isinstance(competitor, dict):
                    continue
                team = competitor.get("team")
                if isinstance(team, dict) and team.get("$ref"):
                    team_refs.append(self._https_url(str(team.get("$ref"))))
            team_results = await asyncio.gather(
                *(self._fetch_absolute(ref, {}) for ref in team_refs),
                return_exceptions=True,
            )
            team_by_ref = {
                ref: result
                for ref, result in zip(team_refs, team_results, strict=True)
                if isinstance(result, dict)
            }
            for competitor in competitors:
                if not isinstance(competitor, dict):
                    continue
                team = competitor.get("team")
                if isinstance(team, dict) and team.get("$ref"):
                    hydrated_team = team_by_ref.get(self._https_url(str(team.get("$ref"))))
                    if hydrated_team:
                        competitor["team"] = hydrated_team
        return event

    async def _fetch(self, endpoint: str, params: dict[str, EspnParam]) -> dict[str, Any]:
        async with self._request_lock:
            loop = asyncio.get_running_loop()
            wait_seconds = self._next_request_at - loop.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._request_interval
            response = await self._client.get(endpoint, params=params)
        if response.is_error:
            raise RuntimeError(f"ESPN_HTTP_{response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("ESPN_INVALID_RESPONSE")
        return payload

    async def _fetch_absolute(self, url: str, params: dict[str, EspnParam]) -> dict[str, Any]:
        async with self._request_lock:
            loop = asyncio.get_running_loop()
            wait_seconds = self._next_request_at - loop.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._request_interval
            response = await self._client.get(self._https_url(url), params=params)
        if response.is_error:
            raise RuntimeError(f"ESPN_CORE_HTTP_{response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("ESPN_CORE_INVALID_RESPONSE")
        return payload

    def _candidate_leagues(self, competition_key: str) -> tuple[str, ...]:
        mapped = self._competition_to_league(competition_key)
        if mapped and mapped in self._league_paths:
            return (mapped, *(league for league in self._league_paths if league != mapped))
        return self._league_paths

    @staticmethod
    def _competition_to_league(competition_key: str) -> str:
        normalized = competition_key.casefold().replace("-", "_").replace(" ", "_")
        mapping = {
            "epl": "eng.1",
            "premier_league": "eng.1",
            "laliga": "esp.1",
            "la_liga": "esp.1",
            "serie_a": "ita.1",
            "bundesliga": "ger.1",
            "ligue_1": "fra.1",
            "eredivisie": "ned.1",
            "primeira": "por.1",
            "liga_portugal": "por.1",
            "super_lig": "tur.1",
            "championship": "eng.2",
            "mls": "usa.1",
            "ucl": "uefa.champions",
            "champions_league": "uefa.champions",
        }
        return mapping.get(normalized, "")

    @classmethod
    def _match_event(
        cls, fixture: CanonicalFixture, events: tuple[dict[str, Any], ...]
    ) -> dict[str, Any]:
        target_home = cls._normalize(fixture.home_team)
        target_away = cls._normalize(fixture.away_team)
        target_date = fixture.kickoff_at.astimezone(UTC).date().isoformat()
        for event in events:
            home_team, away_team = cls._competitor_teams(event)
            event_date = str(event.get("date") or "")[:10]
            if (
                cls._team_matches(home_team, target_home)
                and cls._team_matches(away_team, target_away)
                and event_date == target_date
            ):
                return event
        for event in events:
            home_team, away_team = cls._competitor_teams(event)
            if cls._team_matches(home_team, target_home) and cls._team_matches(
                away_team, target_away
            ):
                return event
        return {}

    @classmethod
    def _team_matches(cls, team: dict[str, Any], target: str) -> bool:
        names = (
            team.get("displayName"),
            team.get("name"),
            team.get("shortDisplayName"),
            team.get("abbreviation"),
        )
        normalized_names = {cls._normalize(str(name)) for name in names if name}
        return target in normalized_names or any(
            target in candidate or candidate in target for candidate in normalized_names
        )

    @staticmethod
    def _competitor_teams(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        competitors = EspnSoccerProvider._nested(event, "competitions", 0, "competitors")
        if not isinstance(competitors, list):
            return {}, {}
        home_team: dict[str, Any] = {}
        away_team: dict[str, Any] = {}
        for competitor in competitors:
            if not isinstance(competitor, dict):
                continue
            team = competitor.get("team")
            if not isinstance(team, dict):
                continue
            if competitor.get("homeAway") == "home":
                home_team = team
            elif competitor.get("homeAway") == "away":
                away_team = team
        return home_team, away_team

    @staticmethod
    def _summary_record(payload: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = (
            "header",
            "boxscore",
            "gameInfo",
            "injuries",
            "leaders",
            "news",
            "standings",
            "predictor",
            "odds",
        )
        return {key: payload[key] for key in allowed_keys if key in payload}

    @classmethod
    def _news_records(
        cls, payload: dict[str, Any], fixture: CanonicalFixture
    ) -> tuple[dict[str, Any], ...]:
        articles = payload.get("articles")
        if not isinstance(articles, list):
            return ()
        team_terms = (cls._normalize(fixture.home_team), cls._normalize(fixture.away_team))
        relevant: list[dict[str, Any]] = []
        fallback: list[dict[str, Any]] = []
        for article in articles:
            if not isinstance(article, dict):
                continue
            compact = cls._compact_article(article)
            fallback.append(compact)
            haystack = cls._normalize(
                " ".join(
                    str(article.get(key) or "")
                    for key in ("headline", "description", "lastModified", "published")
                )
            )
            if any(term and term in haystack for term in team_terms):
                relevant.append(compact)
        return tuple((relevant or fallback)[:10])

    @staticmethod
    def _compact_article(article: dict[str, Any]) -> dict[str, Any]:
        return {
            key: article.get(key)
            for key in (
                "headline",
                "description",
                "published",
                "lastModified",
                "byline",
                "links",
                "images",
                "categories",
            )
            if key in article
        }

    @staticmethod
    def _list_records(payload: dict[str, Any], key: str) -> tuple[dict[str, Any], ...]:
        records = payload.get(key)
        if not isinstance(records, list):
            return ()
        return tuple(record for record in records if isinstance(record, dict))

    @staticmethod
    def _has_odds_context(artifacts: list[EvidenceArtifact]) -> bool:
        for artifact in artifacts:
            if "odds" in artifact.kind and artifact.records:
                return True
            if artifact.kind == "event_summary" and any("odds" in record for record in artifact.records):
                return True
        return False

    @staticmethod
    def _unmatched_evidence(
        *,
        fixture: CanonicalFixture,
        observed_at: datetime,
        artifacts: list[EvidenceArtifact],
        scanned_events: list[dict[str, Any]],
    ) -> DeepFootballEvidence:
        coverage = {artifact.kind: bool(artifact.records) for artifact in artifacts}
        coverage.update(
            {
                "fixture": False,
                "scoreboard": bool(scanned_events),
                "summary": False,
                "news": False,
                "rosters": False,
                "injuries": False,
                "team_schedules": False,
            }
        )
        return DeepFootballEvidence(
            provider=EspnSoccerProvider.source_name,
            provider_fixture_id=f"unmatched:{fixture.provider_fixture_id or fixture.id}",
            observed_at=observed_at,
            home_team_id=0,
            away_team_id=0,
            league_id=0,
            season=fixture.kickoff_at.year,
            artifacts=tuple(artifacts),
            coverage=coverage,
        )

    @staticmethod
    def _nested(value: Any, *path: str | int) -> Any:
        current = value
        for key in path:
            if isinstance(key, int) and isinstance(current, list) and len(current) > key:
                current = current[key]
            elif isinstance(key, str) and isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    @classmethod
    def _ref_value(cls, value: Any) -> str:
        if isinstance(value, dict) and value.get("$ref"):
            return cls._https_url(str(value.get("$ref")))
        return ""

    @staticmethod
    def _https_url(url: str) -> str:
        if url.startswith("http://"):
            return "https://" + url.removeprefix("http://")
        return url

    @staticmethod
    def _int_value(value: object) -> int:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        plain = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        tokens = (
            token
            for token in plain.replace("&", " ").replace("-", " ").split()
            if token not in {"fc", "cf", "sc", "ac", "ss", "afc", "club", "de", "la"}
        )
        return " ".join(tokens)
