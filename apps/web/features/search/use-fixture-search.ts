"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

export type FixtureSearchItem = {
  id: string;
  competition_name: string;
  home_team: string;
  away_team: string;
  kickoff_at: string;
  source_provider: "mock_fixture" | "openligadb" | "football_data_org";
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function useFixtureSearch(query: string) {
  const [debounced, setDebounced] = useState(query);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);
  return useQuery({
    queryKey: ["fixture-search", debounced],
    enabled: debounced.length >= 2,
    queryFn: async ({ signal }): Promise<FixtureSearchItem[]> => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/fixtures/search?query=${encodeURIComponent(debounced)}`,
        { signal },
      );
      if (!response.ok)
        throw new Error(`FIXTURE_SEARCH_FAILED_${response.status}`);
      const body = (await response.json()) as { items: FixtureSearchItem[] };
      return body.items;
    },
  });
}
