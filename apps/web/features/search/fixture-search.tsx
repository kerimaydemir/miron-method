"use client";

import { useState } from "react";
import { type FixtureSearchItem, useFixtureSearch } from "./use-fixture-search";

function kickoff(value: string) {
  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Istanbul",
  }).format(new Date(value));
}

export function FixtureSearch({
  onSelect,
}: {
  onSelect: (fixture: FixtureSearchItem) => void;
}) {
  const [query, setQuery] = useState("");
  const search = useFixtureSearch(query);
  const isOpen = query.trim().length >= 2;

  return (
    <div className="search-root">
      <div className="search-wrap">
        <span aria-hidden="true">⌕</span>
        <input
          id="match-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Takım veya lig ara"
          aria-label="Maç ara"
          minLength={2}
          autoComplete="off"
          role="combobox"
          aria-expanded={isOpen && Boolean(search.data?.length)}
          aria-controls="fixture-results"
        />
      </div>
      {isOpen ? (
        <div className="search-results" id="fixture-results" role="listbox">
          {search.isPending ? (
            <p>Aranıyor…</p>
          ) : search.isError ? (
            <p>Arama şu anda kullanılamıyor.</p>
          ) : search.data?.length ? (
            search.data.map((item) => (
              <button
                type="button"
                role="option"
                aria-selected="false"
                key={item.id}
                onClick={() => {
                  onSelect(item);
                  setQuery("");
                }}
              >
                <span>
                  <strong>
                    {item.home_team} — {item.away_team}
                  </strong>
                  <small>{item.competition_name}</small>
                </span>
                <time>{kickoff(item.kickoff_at)}</time>
              </button>
            ))
          ) : (
            <p>Eşleşen maç bulunamadı.</p>
          )}
        </div>
      ) : null}
    </div>
  );
}
