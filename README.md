# Stable Indexer

Stable Indexer normalizes USDC and USDT transfers from Base, Ethereum,
Solana, and Tron into PostgreSQL and exposes analytics through FastAPI and
React.

## Configuration

Copy `.env.example` to `.env` and configure the RPC endpoints you want
to index. Base and Ethereum use EVM JSON-RPC endpoints. Solana requires
a mainnet JSON-RPC endpoint that supports finalized `getBlock` requests.
Tron uses a TronGrid API key for its confirmed TRC-20 event API.

```env
SOLANA_RPC_URL=https://your-solana-rpc-provider.example/api-key
TRONGRID_API_KEY=your-trongrid-api-key
```

Solana is enabled only when `SOLANA_RPC_URL` is set. It indexes Circle's
mainnet USDC and Tether's USDT mints. Tron is enabled only when
`TRONGRID_API_KEY` is set and indexes Tether's mainnet USDT contract,
`TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`.

## Startup

```bash
./dev.sh
```

## Historical Backfills

Backfill one chain at a time, beginning at a block or Solana slot your
RPC provider can serve. Use a token deployment or mint-creation point
instead of chain genesis where possible.

```bash
python -m app.indexer.backfill \
  --chain base \
  --start-block <block-or-slot> \
  --rewind
```

`--rewind` is required when moving an existing checkpoint backward. A
backfill holds the chain lock for its full run, causing the live worker
to wait for that chain rather than advance the same checkpoint. Stop it
with `Ctrl+C` and rerun without `--start-block` to resume:

```bash
python -m app.indexer.backfill --chain base
```

For a non-destructive 24-hour EVM replay, let the indexer resolve the
start block from the chain timestamp:

```bash
python -m app.indexer.backfill \
  --chain ethereum \
  --previous-hours 24 \
  --rewind
```

This reprocesses every configured stablecoin on the selected chain. The
transfer uniqueness constraint preserves existing rows and inserts the
new token activity.

Use `--max-syncs` to run a bounded portion of a backfill. Transfer
uniqueness prevents duplicate records when a provider retry or a
rewound range is processed again.

## Daily Indexing

On a new checkpoint, the Base, Ethereum, and Tron workers seed
from the previous 24 hours using the chain's own block timestamps. They
then continue indexing forward normally. The seed is one-time; this is
not a rolling-deletion policy.

To discard all indexed data and the checkpoint for one chain before
starting the daily seed, first stop any importer or worker for that
chain, then run:

```bash
python -m app.indexer.reset --chain base --confirm
```

The next `python -m app.indexer.worker` run initializes Base from the
previous 24 hours. Resetting a chain deletes every stored transfer for
that chain, including earlier live-indexed records.

## Dashboard Metric Rollups

Dashboard summary, daily activity, and Top Addresses use incremental
PostgreSQL rollups rather than scanning raw transfers. New indexed and
imported transfers update these rollups automatically.

After loading transfers outside the application, rebuild the rollups:

```bash
python -m app.indexer.rebuild_metrics
```

Use `--chain base` to rebuild one enabled chain. The command waits for
the chain locks, so workers safely resume after it completes.

## Fast EVM Historical Imports

For a complete Base or Ethereum USDC history, use an Alchemy RPC URL in
`BASE_RPC_URL` or `ETHEREUM_RPC_URL`. The importer uses Alchemy's
paginated ERC-20 Transfers API, writes the same normalized records as
the live indexer, and updates the chain checkpoint only after the full
range completes.

```bash
python -m app.indexer.import_history \
  --chain base \
  --start-block 2797221
```

Use Ethereum USDC's deployment block for Ethereum:

```bash
python -m app.indexer.import_history \
  --chain ethereum \
  --start-block 6082465
```

The importer holds the per-chain advisory lock, so the corresponding
live worker waits until the import finishes. A bounded smoke test can
be run with `--max-pages 1`; it writes that page but deliberately does
not move the checkpoint. Do not use it as a resumable import mode.

Solana's current Helius transfer API accepts an owner wallet and cannot
enumerate all transfers for a mint. The regular Solana indexer remains
the supported path until a mint-wide historical dataset provider is
integrated.
