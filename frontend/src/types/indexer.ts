export interface IndexerStatus {
  chain: string;
  latest_block: number;
  last_processed_block: number | null;
  blocks_behind: number | null;
  caught_up: boolean;
  updated_at: string | null;
}