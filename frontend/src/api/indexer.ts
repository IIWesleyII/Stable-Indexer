import type { IndexerStatus } from "../types/indexer";

export async function getIndexerStatus(): Promise<IndexerStatus[]> {
  const response = await fetch("/api/indexer/status");

  if (!response.ok) {
    throw new Error("Failed to load indexer status");
  }

  return response.json();
}
