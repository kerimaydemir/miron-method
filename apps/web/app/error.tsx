"use client";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="shell">
      <section className="panel error-panel">
        <h1>Bir şey ters gitti</h1>
        <p>Güvenli biçimde yeniden deneyebilirsin.</p>
        <button type="button" onClick={reset}>
          Yeniden dene
        </button>
      </section>
    </main>
  );
}
