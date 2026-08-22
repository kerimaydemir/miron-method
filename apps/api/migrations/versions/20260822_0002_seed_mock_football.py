"""Seed deterministic mock football identities.

Revision ID: 20260822_0002
Revises: 20260822_0001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260822_0002"
down_revision: str | None = "20260822_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    INSERT INTO sports (id, sport_key, plugin_key)
    VALUES ('92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'football', 'football.v1')
    ON CONFLICT DO NOTHING;

    INSERT INTO competitions (id, sport_id, competition_key, name, country_code) VALUES
      ('478b2d55-48b7-5fe9-975a-4344ee80e4e9', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'TR-SEED', 'Marmara Ligi', 'TR'),
      ('601dae36-6e5f-5e4e-ad43-89ba91f5134d', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'TR-CUP', 'Anadolu Kupası', 'TR')
    ON CONFLICT DO NOTHING;

    INSERT INTO teams (id, sport_id, name, country_code) VALUES
      ('4a72e8c8-4848-5bb2-99a8-b70187cdcf1c', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Anka FK', 'TR'),
      ('7e0c2366-5c44-58c1-a830-f76ddc523ed2', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Boğaz SK', 'TR'),
      ('e8259185-6ca4-5c69-8055-0910b3043b5b', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Marmara 1923', 'TR'),
      ('875c9432-d4db-5049-bec0-fbc568b9e2bf', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Ege Atletik', 'TR'),
      ('dff6f381-f6f7-56e8-adad-7260654662dc', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Toros Birlik', 'TR'),
      ('ba8dcfba-1301-530c-9d6d-4361e95054e0', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Trakya Spor', 'TR'),
      ('f2be96c3-fa8c-55e0-b8d0-bf8132335589', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Başkent Gücü', 'TR'),
      ('57877ebf-48b0-5fa5-aa95-fcd0c1e65e8b', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', 'Karadeniz FK', 'TR')
    ON CONFLICT DO NOTHING;

    INSERT INTO fixtures
      (id, sport_id, competition_id, home_team_id, away_team_id, kickoff_at, status)
    VALUES
      ('958ca732-f3ed-5782-8cec-97bcedf941e7', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', '478b2d55-48b7-5fe9-975a-4344ee80e4e9', '4a72e8c8-4848-5bb2-99a8-b70187cdcf1c', '7e0c2366-5c44-58c1-a830-f76ddc523ed2', '2026-08-22T17:00:00Z', 'scheduled'),
      ('0e6b424d-081d-5382-8cb3-0b855212fd8d', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', '478b2d55-48b7-5fe9-975a-4344ee80e4e9', 'e8259185-6ca4-5c69-8055-0910b3043b5b', '875c9432-d4db-5049-bec0-fbc568b9e2bf', '2026-08-23T13:00:00Z', 'scheduled'),
      ('1d14d89c-2204-5eba-b0c6-fa96b784e961', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', '478b2d55-48b7-5fe9-975a-4344ee80e4e9', 'dff6f381-f6f7-56e8-adad-7260654662dc', 'ba8dcfba-1301-530c-9d6d-4361e95054e0', '2026-08-24T18:45:00Z', 'scheduled'),
      ('d4ff04e9-b8dd-58e1-9cf8-48d3b0fa6c51', '92e3fa97-f0c3-5298-83f7-1bf958ad4879', '601dae36-6e5f-5e4e-ad43-89ba91f5134d', 'f2be96c3-fa8c-55e0-b8d0-bf8132335589', '57877ebf-48b0-5fa5-aa95-fcd0c1e65e8b', '2026-08-24T20:30:00Z', 'scheduled')
    ON CONFLICT DO NOTHING;

    INSERT INTO fixture_versions (fixture_id, version, kickoff_at, status, observed_at)
    SELECT id, 1, kickoff_at, status, '2026-08-22T00:00:00Z'
    FROM fixtures
    WHERE id IN (
      '958ca732-f3ed-5782-8cec-97bcedf941e7',
      '0e6b424d-081d-5382-8cb3-0b855212fd8d',
      '1d14d89c-2204-5eba-b0c6-fa96b784e961',
      'd4ff04e9-b8dd-58e1-9cf8-48d3b0fa6c51'
    )
    ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
    DELETE FROM fixture_versions WHERE fixture_id IN (
      '958ca732-f3ed-5782-8cec-97bcedf941e7',
      '0e6b424d-081d-5382-8cb3-0b855212fd8d',
      '1d14d89c-2204-5eba-b0c6-fa96b784e961',
      'd4ff04e9-b8dd-58e1-9cf8-48d3b0fa6c51'
    );
    DELETE FROM fixtures WHERE id IN (
      '958ca732-f3ed-5782-8cec-97bcedf941e7',
      '0e6b424d-081d-5382-8cb3-0b855212fd8d',
      '1d14d89c-2204-5eba-b0c6-fa96b784e961',
      'd4ff04e9-b8dd-58e1-9cf8-48d3b0fa6c51'
    );
    DELETE FROM teams WHERE sport_id = '92e3fa97-f0c3-5298-83f7-1bf958ad4879';
    DELETE FROM competitions WHERE sport_id = '92e3fa97-f0c3-5298-83f7-1bf958ad4879';
    DELETE FROM sports WHERE id = '92e3fa97-f0c3-5298-83f7-1bf958ad4879';
    """)
