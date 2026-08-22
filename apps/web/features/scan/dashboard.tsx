"use client";

import Link from "next/link";
import { useState } from "react";
import { StartAnalysisButton } from "@/features/analysis/start-analysis-button";
import { FixtureSearch } from "@/features/search/fixture-search";
import type { FixtureSearchItem } from "@/features/search/use-fixture-search";
import { useScan } from "./use-scan";

const DATE_LABELS = ["Bugün", "Yarın", "+2 gün"] as const;

function formatDate(value: string | undefined, fallback: string) {
  if (!value) return fallback;
  return new Intl.DateTimeFormat("tr-TR", {
    day: "numeric",
    month: "short",
    timeZone: "Europe/Istanbul",
  }).format(new Date(`${value}T12:00:00+03:00`));
}

function formatKickoff(value: string) {
  return new Intl.DateTimeFormat("tr-TR", {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Istanbul",
  }).format(new Date(value));
}

function formatObserved(value: string | null | undefined) {
  if (!value) return "Henüz senkronize edilmedi";
  return `Son veri ${new Intl.DateTimeFormat("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Europe/Istanbul",
  }).format(new Date(value))}`;
}

export function Dashboard() {
  const scan = useScan();
  const [selected, setSelected] = useState<FixtureSearchItem | null>(null);
  const candidates = scan.data?.candidates ?? [];

  return (
    <main className="shell home-shell">
      <header className="brand-bar">
        <Link className="brand" href="/" aria-label="MİRON BABA AI ana sayfa">
          <span className="brand-mark" aria-hidden="true">
            M
          </span>
          <span>
            <strong>MİRON BABA</strong>
            <small>Football intelligence</small>
          </span>
        </Link>
        <div className="top-actions">
          <Link className="nav-link" href="/auto">
            Otomatik Kupon
          </Link>
          <div className="model-status">
            <span className="model-dots" aria-hidden="true">
              <i />
              <i />
              <i />
              <i />
            </span>
            Gemini-only rota
          </div>
        </div>
      </header>

      <section className="ai-hero" aria-labelledby="hero-title">
        <div className="online-pill">
          <i aria-hidden="true" /> Canlı fikstür · Gemini aktif
        </div>
        <h1 id="hero-title">
          Maçı seç.
          <span>AI tartışsın.</span>
        </h1>
        <p>
          Üç günlük fikstürü tarar, veriyi tartar ve sana tek, açıklanabilir bir
          tahmin bırakır.
        </p>

        <div className="ai-command">
          <div className="command-search">
            <FixtureSearch onSelect={setSelected} />
          </div>
          <button
            className="scan-button"
            type="button"
            disabled={scan.isPending}
            onClick={() => scan.mutate()}
          >
            <span aria-hidden="true">✦</span>
            {scan.isPending ? "Taranıyor…" : "3 günü tara"}
          </button>
        </div>

        <div className="date-line" aria-label="Tarama tarihleri">
          {DATE_LABELS.map((label, index) => {
            const date = scan.data?.local_dates[index];
            const count = date
              ? candidates.filter(
                  (item) => item.fixture.kickoff_at.slice(0, 10) === date,
                ).length
              : 0;
            return (
              <span key={label}>
                <strong>{formatDate(date, label)}</strong>
                {scan.data ? `${count} maç` : label}
              </span>
            );
          })}
        </div>
      </section>

      {selected ? (
        <aside className="selection-card">
          <span className="selection-icon" aria-hidden="true">
            ✦
          </span>
          <div>
            <small>Seçilen maç</small>
            <strong>
              {selected.home_team} — {selected.away_team}
            </strong>
            <p>
              {selected.competition_name} ·{" "}
              {selected.source_provider === "mock_fixture"
                ? "Pilot veri"
                : "Canlı feed"}
            </p>
          </div>
          <StartAnalysisButton fixtureId={selected.id}>
            Analizi başlat →
          </StartAnalysisButton>
        </aside>
      ) : null}

      <section className="results-section" aria-labelledby="results-title">
        <div className="results-head">
          <div>
            <small>AI seçimi</small>
            <h2 id="results-title">Analize değer maçlar</h2>
          </div>
          <span>
            {scan.isPending
              ? "Fikstür taranıyor"
              : scan.data
                ? `${candidates.length} sonuç · ${formatObserved(scan.data.source_observed_at)}`
                : "Henüz taranmadı"}
          </span>
        </div>

        {scan.isError ? (
          <div className="simple-empty" role="alert">
            <span>!</span>
            <div>
              <strong>Tarama tamamlanamadı</strong>
              <p>API bağlantısını kontrol edip yeniden dene.</p>
            </div>
          </div>
        ) : candidates.length > 0 ? (
          <div className="fixture-list">
            {candidates.map((candidate, index) => (
              <article
                className={`fixture-row ${index === 0 ? "featured" : ""}`}
                key={candidate.fixture.id}
              >
                <div className="score-ring">
                  <strong>{candidate.worthwhile_score}</strong>
                  <small>AI skor</small>
                </div>
                <div className="fixture-main">
                  <small>
                    {candidate.fixture.competition_name} ·{" "}
                    {formatKickoff(candidate.fixture.kickoff_at)}
                  </small>
                  <h3>
                    {candidate.fixture.home_team}
                    <span>—</span>
                    {candidate.fixture.away_team}
                  </h3>
                  <p>
                    {candidate.positive_factors[0]} · Veri{" "}
                    {candidate.coverage_label.toLocaleLowerCase("tr-TR")} · $
                    {candidate.estimated_cost_usd}
                  </p>
                </div>
                <StartAnalysisButton fixtureId={candidate.fixture.id}>
                  İncele ↗
                </StartAnalysisButton>
              </article>
            ))}
          </div>
        ) : (
          <div className="simple-empty">
            <div className="ai-orb" aria-hidden="true">
              <i />
            </div>
            <div>
              <strong>Hazırım.</strong>
              <p>Bugün, yarın ve sonraki günün maçlarını birlikte tarayalım.</p>
            </div>
          </div>
        )}
      </section>

      <footer className="minimal-footer">
        <span>MİRON BABA AI</span>
        <span>
          football-data.org / OpenLigaDB · Gemini-only · Bahis tavsiyesi
          değildir
        </span>
      </footer>
    </main>
  );
}
