# Stable Indexer - Agent Instructions

## Project Overview

Stable Indexer is a multi-chain stablecoin indexing and analytics platform.

The system continuously indexes stablecoin transfer events from blockchain
networks, normalizes them into a chain-neutral data model, stores them in
PostgreSQL, exposes analytics through FastAPI, and displays those analytics in
a React/TypeScript frontend.

The long-term goal is to support:

- Base
- Ethereum
- Solana
- Multiple stablecoins
- Cross-chain analytics
- Address exploration
- Watchlists
- Stablecoin supply analytics
- Historical backfills

The architecture should remain extensible to additional chains and tokens.


## Core Architecture

The intended data flow is:

```text
Blockchain adapters
        ↓
IndexedTransfer
        ↓
PostgreSQL
        ↓
FastAPI
        ↓
React