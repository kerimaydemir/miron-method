"use client";

import Link from "next/link";
import type { StageDossier } from "./types";
import {
  useAnalysisEvidence,
  useAnalysisRun,
  useLockAnalysis,
} from "./use-analysis";

const LABELS = { home: "Ev", draw: "Beraberlik", away: "Deplasman" } as const;
const PROVIDER_LABELS = {
  mock: "Deneme verisi · mock",
  google_gemini: "Google Gemini",
  nvidia_nim: "NVIDIA NIM",
} as const;

function DetailedStageDossier({ dossier }: { dossier: StageDossier }) {
  const groups: Array<[string, string[] | undefined]> = [
    ["Bulgular", dossier.findings],
    ["Kanıt referansları", dossier.evidence_refs],
    ["Karşı argümanlar", dossier.counterpoints],
    ["Bilinmeyenler", dossier.unknowns],
    ["Takım haberleri", dossier.team_news],
    ["Teknik direktör", dossier.coach_notes],
    ["Muhtemel 11", dossier.likely_lineups],
    ["Oyuncular", dossier.player_notes],
    ["Kaynaklar", dossier.citations],
  ];
  return (
    <details className="stage-dossier">
      <summary>Ayrıntılı kanıt dosyası</summary>
      {groups.map(([label, items]) =>
        items && items.length > 0 ? (
          <section key={label}>
            <strong>{label}</strong>
            <ul>
              {items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null,
      )}
    </details>
  );
}

export function RunView({ runId }: { runId: string }) {
  const run = useAnalysisRun(runId);
  const evidence = useAnalysisEvidence(runId);
  const lock = useLockAnalysis(runId);

  if (run.isPending) {
    return (
      <main className="shell">
        <div
          className="skeleton"
          role="status"
          aria-label="Analiz yükleniyor"
        />
      </main>
    );
  }

  if (run.isError || !run.data) {
    return (
      <main className="shell">
        <section className="error-panel">
          <span>!</span>
          <h1>Analiz yüklenemedi</h1>
          <Link href="/">Ana ekrana dön</Link>
        </section>
      </main>
    );
  }

  const data = run.data;
  const isMock = data.forecast.analysis_provider === "mock";
  const providerLabel = PROVIDER_LABELS[data.forecast.analysis_provider];
  const displayedModels = [...new Set(data.forecast.model_ids.filter(Boolean))];
  const leader = data.forecast.outcome_probabilities.reduce((best, item) =>
    Number(item.probability) > Number(best.probability) ? item : best,
  );

  return (
    <main className="shell run-shell">
      <header className="run-topbar">
        <Link href="/">← Yeni analiz</Link>
        <div className="model-status">
          <span className="model-dots" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
          </span>
          {providerLabel}
        </div>
      </header>

      <section className="result-hero">
        <div className="result-kicker">
          <span className={data.state === "LOCKED" ? "locked" : ""}>
            {data.state === "LOCKED" ? "Kilitli tahmin" : "Analiz tamamlandı"}
          </span>
          <small>{data.stages.length} kayıtlı aşama</small>
        </div>
        <h1>
          {LABELS[leader.outcome]}
          <span>%{Math.round(Number(leader.probability) * 100)}</span>
        </h1>
        <p>
          {isMock
            ? "Bu sonuç deneme modunda üretildi; gerçek bir model tahmini değildir."
            : `${providerLabel} ile üretilen bu analizin kayıtlı modelleri ve kanıtları aşağıda.`}{" "}
          Olasılıklar ön değerlendirmedir; ölçülmüş başarı oranı değildir.
        </p>

        <div className="probability-stack" aria-label="Sonuç olasılıkları">
          <div className="probability-bar" aria-hidden="true">
            {data.forecast.outcome_probabilities.map((item) => (
              <i
                className={`probability-${item.outcome}`}
                style={{ width: `${Number(item.probability) * 100}%` }}
                key={item.outcome}
              />
            ))}
          </div>
          <div className="probability-labels">
            {data.forecast.outcome_probabilities.map((item) => (
              <span key={item.outcome}>
                <small>{LABELS[item.outcome]}</small>
                <strong>%{Math.round(Number(item.probability) * 100)}</strong>
                <em>
                  %{Math.round(Number(item.lower) * 100)}–%
                  {Math.round(Number(item.upper) * 100)}
                </em>
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="model-rail" aria-label="Bu analizde kayıtlı modeller">
        {displayedModels.length === 0 ? (
          <article>
            <div>
              <strong>{isMock ? "Mock çalışma" : "Model kaydı yok"}</strong>
              <small>Bu çalışma için model adı bildirilmedi.</small>
            </div>
          </article>
        ) : (
          displayedModels.map((modelId, index) => (
            <article key={modelId}>
              <span>{index + 1}</span>
              <div>
                <strong>{modelId}</strong>
                <small>{isMock ? "Mock kaydındaki model" : "Çalışma kaydı"}</small>
              </div>
            </article>
          ))
        )}
      </section>

      <section className="insight-grid">
        <article>
          <span className="insight-icon positive" aria-hidden="true">
            ↗
          </span>
          <small>Neden bu sonuç?</small>
          <h2>{data.forecast.decisive_evidence[0]}</h2>
          <p>{data.forecast.decisive_evidence[1]}</p>
        </article>
        <article>
          <span className="insight-icon caution" aria-hidden="true">
            ∿
          </span>
          <small>En büyük belirsizlik</small>
          <h2>{data.forecast.uncertainty_drivers[0]}</h2>
          <p>{data.forecast.uncertainty_drivers[1]}</p>
        </article>
        <article className="compact-metrics">
          <div>
            <small>Güven</small>
            <strong>
              %{Math.round(Number(data.forecast.confidence) * 100)}
            </strong>
          </div>
          <div>
            <small>Kaydedilen maliyet</small>
            <strong>${data.actual_cost_usd}</strong>
          </div>
          <div>
            <small>Kalibrasyon</small>
            <strong>
              {data.forecast.calibration_status === "provisional"
                ? "Ön değerlendirme"
                : data.forecast.calibration_status}
            </strong>
          </div>
        </article>
      </section>

      <details className="audit-details">
        <summary>
          <span>
            <strong>{data.stages.length} aşamalı denetim izi</strong>
            <small>Kanıt, quant, eleştiri ve sentez adımlarının tamamı</small>
          </span>
          <span aria-hidden="true">+</span>
        </summary>
        <div className="stage-list">
          {data.stages.map((stage) => (
            <article key={stage.stage_id}>
              <span className="stage-check">✓</span>
              <div>
                <strong>
                  {stage.stage_id} · {stage.name}
                </strong>
                <p>{stage.summary}</p>
                {evidence.data?.stage_outputs[stage.stage_id] ? (
                  <DetailedStageDossier
                    dossier={evidence.data.stage_outputs[stage.stage_id]!}
                  />
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </details>

      <p className="responsible-notice">
        {data.forecast.responsible_use_notice}
      </p>

      <section
        className={`lock-dock ${data.state === "LOCKED" ? "is-locked" : ""}`}
      >
        <div>
          <small>Tahmin bütünlüğü</small>
          <strong>
            {data.state === "LOCKED"
              ? "Tahmin değiştirilemez"
              : "Tahmini şimdi kilitle"}
          </strong>
          <p>
            {data.lock_sha256 ??
              "Cutoff, model rotaları ve bütün kanıtlar hash'lenir."}
          </p>
        </div>
        {data.state === "LOCKED" ? (
          <span className="verified-badge">✓ SHA-256 doğrulandı</span>
        ) : (
          <button
            type="button"
            disabled={lock.isPending}
            onClick={() => lock.mutate()}
          >
            {lock.isPending ? "Kilitleniyor…" : "Tahmini kilitle"}
          </button>
        )}
      </section>
    </main>
  );
}
