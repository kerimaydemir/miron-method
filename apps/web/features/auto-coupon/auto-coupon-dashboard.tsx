"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import type { CouponSelection } from "./types";
import { useAutoCoupon } from "./use-auto-coupon";

const DEFAULT_LEAGUES = [
  { key: "epl", name: "Premier League" },
  { key: "laliga", name: "LaLiga" },
  { key: "bundesliga", name: "Bundesliga" },
  { key: "serie_a", name: "Serie A" },
  { key: "ligue_1", name: "Ligue 1" },
  { key: "eredivisie", name: "Eredivisie" },
  { key: "primeira", name: "Primeira Liga" },
  { key: "super_lig", name: "Süper Lig" },
] as const;

function formatKickoff(value: string) {
  return new Intl.DateTimeFormat("tr-TR", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Istanbul",
  }).format(new Date(value));
}

function selectionNames(fixtureIds: string[], selections: CouponSelection[]) {
  return fixtureIds
    .map((id) => {
      const item = selections.find((selection) => selection.fixture.id === id);
      return item
        ? `${item.fixture.home_team}–${item.fixture.away_team}: ${item.market_label} / ${item.outcome_label}`
        : null;
    })
    .filter(Boolean)
    .join(" · ");
}

export function AutoCouponDashboard({
  initialRunId,
}: {
  initialRunId?: string;
}) {
  const auto = useAutoCoupon(initialRunId);
  const data = auto.data ?? (!initialRunId ? auto.journal?.[0] : undefined);
  const readiness = auto.readiness;
  const errorMessage = auto.error?.message ?? "UNKNOWN_AUTO_COUPON_ERROR";
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (data && pathname !== `/auto/${data.run_id}`) {
      router.replace(`/auto/${data.run_id}`);
    }
  }, [data, pathname, router]);

  return (
    <main className="shell auto-shell">
      <header className="brand-bar">
        <Link className="brand" href="/" aria-label="MİRON BABA AI ana sayfa">
          <span className="brand-mark" aria-hidden="true">
            M
          </span>
          <span>
            <strong>MİRON BABA</strong>
            <small>Auto coupon lab</small>
          </span>
        </Link>
        <Link className="nav-link" href="/">
          Manuel analiz
        </Link>
      </header>

      <section className="auto-hero" aria-labelledby="auto-title">
        <div className="online-pill">
          <i aria-hidden="true" /> Tam otomatik · canlı piyasa
        </div>
        <h1 id="auto-title">
          Değeri tara.<span>Gerekirse pas geç.</span>
        </h1>
        <p>
          On büyük ligi ve güncel bookmaker pazarlarını tarar. Derin model
          seçimi varsa %70 kapısını uygular; model kapalıysa sonucu açıkça
          piyasa konsensüsü diye etiketler. Kupon oranı en az 1.80 olur.
        </p>
        <button
          className="auto-start"
          type="button"
          disabled={auto.isPending || readiness?.ready === false}
          onClick={() => auto.mutate()}
        >
          <span aria-hidden="true">✦</span>
          {auto.isPending
            ? "Canlı veri kontrol ediliyor…"
            : readiness?.ready === false
              ? "Veri bağlantıları eksik"
              : "En iyi maçları bul"}
        </button>
        {readiness ? (
          <p
            className={
              readiness.ready
                ? "auto-readiness ready"
                : "auto-readiness blocked"
            }
          >
            <strong>
              {readiness.ready ? "Sistem hazır" : "Üretim durduruldu"}
            </strong>
            {readiness.notice}
            <span>
              Canlı oran: {readiness.live_bookmaker_odds ? "hazır" : "eksik"} ·
              Derin veri: {readiness.deep_structured_data ? "hazır" : "eksik"} ·
              Derin aşama: {readiness.implemented_analysis_stages.length}/
              {readiness.required_analysis_stages.length}
            </span>
          </p>
        ) : null}
        <div className="league-cloud" aria-label="İzinli ligler">
          {(data?.allowed_leagues ?? DEFAULT_LEAGUES).map((league) => (
            <span
              className={
                data?.covered_league_keys.includes(league.key) ? "covered" : ""
              }
              key={league.key}
            >
              {league.name}
            </span>
          ))}
        </div>
      </section>

      {auto.performance ? (
        <section className="funnel-strip" aria-label="Öğrenme metrikleri">
          <div>
            <small>Sonuçlanan</small>
            <strong>{auto.performance.settled}</strong>
            <span>{auto.performance.sample_size_status}</span>
          </div>
          <div>
            <small>İsabet</small>
            <strong>
              {auto.performance.hit_rate
                ? `%${(Number(auto.performance.hit_rate) * 100).toFixed(1)}`
                : "—"}
            </strong>
            <span>
              {auto.performance.wins} kazandı · {auto.performance.losses}{" "}
              kaybetti
            </span>
          </div>
          <div>
            <small>Brier hata</small>
            <strong>{auto.performance.brier_score ?? "—"}</strong>
            <span>olasılık kalibrasyonu</span>
          </div>
          <div className="final">
            <small>Eşit birim ROI</small>
            <strong>
              {auto.performance.equal_stake_roi
                ? `%${(Number(auto.performance.equal_stake_roi) * 100).toFixed(1)}`
                : "—"}
            </strong>
            <span>gerçek para değil</span>
          </div>
        </section>
      ) : null}

      {auto.isPending ? (
        <section className="auto-progress" role="status">
          <div>
            <strong>01</strong>
            <span>Bugünün fikstür ve oran havuzu</span>
          </div>
          <div>
            <strong>02</strong>
            <span>Ucuz Gemini ile kaba eleme</span>
          </div>
          <div>
            <strong>03</strong>
            <span>Eleştirmen ile 0–3 değer adayı</span>
          </div>
          <div>
            <strong>04</strong>
            <span>Çoklu Gemini kurulu ve kilit</span>
          </div>
        </section>
      ) : null}

      {auto.isError ? (
        <section className="auto-error" role="alert">
          <strong>Otomatik seçim tamamlanamadı.</strong>
          <p>
            {errorMessage.includes("LIVE_MARKET_REQUIRED")
              ? "Gerçek ve taze bookmaker verisi bağlı değil. Tahmini oran üretilmedi."
              : errorMessage.includes("DEEP_ANALYSIS_NOT_READY")
                ? "Kadro, form, istatistik, taktik, yorgunluk ve piyasa eleştirisi aşamaları tamamlanmadan kupon üretilmez."
                : errorMessage.includes("DEEP_DATA_REQUIRED")
                  ? "API-Football derin veri bağlantısı olmadan kupon üretilmez."
                  : errorMessage.includes("NOT_ENOUGH")
                    ? "Şu an izinli büyük liglerde en az üç güncel maç yok. Eski veya alt lig maçı eklenmedi."
                    : `Hata: ${errorMessage}`}
          </p>
        </section>
      ) : null}

      {data && data.selections.length === 0 ? (
        <section className="auto-error" role="status">
          <strong>Bugün zorunlu kupon yok.</strong>
          <p>{data.notice}</p>
        </section>
      ) : null}

      {data && data.daily_predictions.length > 0 ? (
        <section className="auto-section" aria-labelledby="daily-journal-title">
          <div className="auto-section-head">
            <div>
              <small>Günlük jurnal</small>
              <h2 id="daily-journal-title">Bugünün takip tahminleri</h2>
            </div>
            <span>{formatKickoff(data.observed_at)}</span>
          </div>
          <div className="pick-grid">
            {data.daily_predictions.map((prediction, index) => (
              <article key={prediction.prediction_id}>
                <div className="pick-rank">0{index + 1}</div>
                <small>
                  {prediction.league.name} ·{" "}
                  {formatKickoff(prediction.fixture.kickoff_at)}
                </small>
                <h3>
                  {prediction.fixture.home_team}
                  <span>—</span>
                  {prediction.fixture.away_team}
                </h3>
                <div className="pick-call">
                  <strong>
                    {prediction.market_label} · {prediction.outcome_label}
                  </strong>
                  <b>%{Math.round(Number(prediction.probability) * 100)}</b>
                </div>
                <div className="odds-line">
                  <span>
                    <small>Oran</small>
                    <strong>{prediction.market_decimal_odds ?? "yok"}</strong>
                  </span>
                  <span>
                    <small>Tier</small>
                    <strong>{prediction.tier.replace("_", " ")}</strong>
                  </span>
                  <span>
                    <small>Bookmaker</small>
                    <strong>{prediction.bookmaker_count}</strong>
                  </span>
                </div>
                <p>{prediction.reasons.join(" ")}</p>
                <em>Risk: {prediction.risks.join(" ")}</em>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {data?.post_match_review ? (
        <section className="auto-section" aria-labelledby="review-title">
          <div className="auto-section-head">
            <div>
              <small>Ertesi gün kontrol</small>
              <h2 id="review-title">Önceki tahminlerin otopsisi</h2>
            </div>
            <span>
              {data.post_match_review.wins} tuttu ·{" "}
              {data.post_match_review.losses} kaybetti ·{" "}
              {data.post_match_review.voids} void
            </span>
          </div>
          <div className="ticket-list">
            {data.post_match_review.items.map((item) => (
              <article key={item.prediction_id}>
                <span
                  className={`risk-${item.status === "won" ? "single" : "treble"}`}
                >
                  {item.status}
                </span>
                <div>
                  <strong>
                    {item.final_home_score}-{item.final_away_score} ·{" "}
                    {item.process_verdict}
                  </strong>
                  <p>{item.explanation}</p>
                  <p>{item.lesson}</p>
                </div>
              </article>
            ))}
          </div>
          <p className="responsible-notice">{data.post_match_review.summary}</p>
        </section>
      ) : null}

      {data && data.selections.length > 0 ? (
        <>
          <section className="funnel-strip" aria-label="Eleme özeti">
            <div>
              <small>Canlı havuz</small>
              <strong>{data.initial_candidates.length}</strong>
              <span>yüksek puanlı maç</span>
            </div>
            <b>→</b>
            <div>
              <small>Kaba eleme</small>
              <strong>{data.rough_decision.selected_fixture_ids.length}</strong>
              <span>{data.rough_decision.model_id}</span>
            </div>
            <b>→</b>
            <div>
              <small>Eleştirmen</small>
              <strong>
                {data.critic_decision.selected_fixture_ids.length}
              </strong>
              <span>{data.critic_decision.model_id}</span>
            </div>
            <b>→</b>
            <div className="final">
              <small>Kilitli seçim</small>
              <strong>{data.selections.length}</strong>
              <span>MİRON BABA</span>
            </div>
          </section>

          <section className="auto-section" aria-labelledby="final-three-title">
            <div className="auto-section-head">
              <div>
                <small>Dinamik seçim</small>
                <h2 id="final-three-title">
                  En güçlü fiyat + olasılık dengesi
                </h2>
              </div>
              <span>
                {data.source_mode === "bookmaker_live"
                  ? "Canlı bookmaker ortalaması"
                  : "Geçersiz eski çalışma"}
              </span>
            </div>
            <div className="pick-grid">
              {data.selections.map((selection, index) => (
                <article key={selection.fixture.id}>
                  <div className="pick-rank">0{index + 1}</div>
                  <small>
                    {selection.league.name} ·{" "}
                    {formatKickoff(selection.fixture.kickoff_at)}
                  </small>
                  <h3>
                    {selection.fixture.home_team}
                    <span>—</span>
                    {selection.fixture.away_team}
                  </h3>
                  <div className="pick-call">
                    <strong>
                      {selection.market_label} · {selection.outcome_label}
                    </strong>
                    <b>%{Math.round(Number(selection.probability) * 100)}</b>
                  </div>
                  <div className="odds-line">
                    <span>
                      <small>Canlı oran</small>
                      <strong>{selection.market_decimal_odds ?? "—"}</strong>
                    </span>
                    <span>
                      <small>Bookmaker</small>
                      <strong>{selection.bookmaker_count}</strong>
                    </span>
                    <span>
                      <small>Edge</small>
                      <strong>
                        {selection.edge
                          ? `%${(Number(selection.edge) * 100).toFixed(1)}`
                          : "—"}
                      </strong>
                    </span>
                  </div>
                  <p>{selection.reason}</p>
                  {selection.rationale ? (
                    <p>{selection.rationale.market_thesis}</p>
                  ) : null}
                  <em>Risk: {selection.uncertainty}</em>
                  {selection.analysis_run_id ? (
                    <Link href={`/runs/${selection.analysis_run_id}`}>
                      Kilitli analizi aç ↗
                    </Link>
                  ) : (
                    <small>
                      Piyasa konsensüsü · {selection.bookmaker ?? "kaynak belirtilmedi"}
                    </small>
                  )}
                </article>
              ))}
            </div>
          </section>

          <section className="auto-section" aria-labelledby="tickets-title">
            <div className="auto-section-head">
              <div>
                <small>Kuponlar</small>
                <h2 id="tickets-title">Riskine göre hazırlandı</h2>
              </div>
              <span>{data.rag_case_count} doğrulanmış vaka kullanıldı</span>
            </div>
            <div className="ticket-list">
              {data.tickets.map((ticket) => (
                <article key={ticket.kind}>
                  <span className={`risk-${ticket.kind}`}>
                    {ticket.risk_label}
                  </span>
                  <div>
                    <strong>{ticket.label}</strong>
                    <p>
                      {selectionNames(
                        ticket.selection_fixture_ids,
                        data.selections,
                      )}
                    </p>
                  </div>
                  <div className="ticket-metric">
                    <small>
                      {ticket.probability_source === "bookmaker_consensus"
                        ? "Piyasa konsensüsü"
                        : "Model ihtimali"}
                    </small>
                    <strong>
                      %{Math.round(Number(ticket.combined_probability) * 100)}
                    </strong>
                  </div>
                  <div className="ticket-metric">
                    <small>
                      {ticket.odds_source === "model_fair_odds"
                        ? "Adil oran"
                        : "Alınabilir oran"}
                    </small>
                    <strong>{ticket.combined_decimal_odds}</strong>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <details className="audit-details auto-audit">
            <summary>
              <span>
                <strong>Eleme gerekçelerini gör</strong>
                <small>İki Gemini kurulunun kısa kararı</small>
              </span>
              <span aria-hidden="true">+</span>
            </summary>
            <div>
              <p>
                <strong>İlk eleme:</strong> {data.rough_decision.rationale}
              </p>
              <p>
                <strong>Son eleme:</strong> {data.critic_decision.rationale}
              </p>
            </div>
          </details>

          <p className="responsible-notice">{data.notice}</p>
        </>
      ) : null}
    </main>
  );
}
