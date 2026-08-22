from unittest import TestCase
from unittest import IsolatedAsyncioTestCase

from app.indexer.backfill import parse_args
from app.indexer.import_history import parse_args as parse_import_args
from app.indexer.reset import parse_args as parse_reset_args
from app.indexer.service import IndexerService


class FakeIndexer:
    chain = "base"

    async def get_block_hash(self, block_number: int) -> str:
        return f"hash-{block_number}"


class FakeSession:
    def __init__(self) -> None:
        self.checkpoint = None
        self.commit_count = 0

    async def get(self, model, chain):
        return self.checkpoint

    def add(self, checkpoint) -> None:
        self.checkpoint = checkpoint

    async def commit(self) -> None:
        self.commit_count += 1


class BackfillArgumentTests(TestCase):
    def test_parse_args_accepts_rewind_with_start_block(self) -> None:
        args = parse_args(
            [
                "--chain",
                "base",
                "--start-block",
                "100",
                "--rewind",
                "--max-syncs",
                "5",
            ]
        )

        self.assertEqual(args.chain, "base")
        self.assertEqual(args.start_block, 100)
        self.assertTrue(args.rewind)
        self.assertEqual(args.max_syncs, 5)

    def test_parse_args_rejects_rewind_without_start_block(self) -> None:
        with self.assertRaises(SystemExit):
            parse_args(["--chain", "base", "--rewind"])

    def test_parse_args_accepts_previous_hours_rewind(self) -> None:
        args = parse_args(
            [
                "--chain",
                "ethereum",
                "--previous-hours",
                "24",
                "--rewind",
            ]
        )

        self.assertEqual(args.previous_hours, 24)
        self.assertTrue(args.rewind)

    def test_parse_args_rejects_previous_hours_without_rewind(self) -> None:
        with self.assertRaises(SystemExit):
            parse_args(
                [
                    "--chain",
                    "ethereum",
                    "--previous-hours",
                    "24",
                ]
            )

    def test_import_args_accept_a_bounded_import(self) -> None:
        args = parse_import_args(
            [
                "--chain",
                "base",
                "--start-block",
                "2797221",
                "--end-block",
                "2798000",
                "--max-pages",
                "1",
            ]
        )

        self.assertEqual(args.chain, "base")
        self.assertEqual(args.start_block, 2797221)
        self.assertEqual(args.end_block, 2798000)
        self.assertEqual(args.max_pages, 1)

    def test_reset_args_require_confirmation(self) -> None:
        with self.assertRaises(SystemExit):
            parse_reset_args(["--chain", "base"])

    def test_reset_args_accept_confirmation(self) -> None:
        args = parse_reset_args(
            ["--chain", "base", "--confirm"]
        )

        self.assertEqual(args.chain, "base")
        self.assertTrue(args.confirm)


class CheckpointRewindTests(IsolatedAsyncioTestCase):
    async def test_rewind_checkpoint_sets_next_block(self) -> None:
        session = FakeSession()
        service = IndexerService(
            session=session,
            indexer=FakeIndexer(),
        )

        result = await service.rewind_checkpoint(100)

        self.assertEqual(result["next_block"], 100)
        self.assertEqual(session.checkpoint.last_processed_block, 99)
        self.assertEqual(session.checkpoint.last_block_hash, "hash-99")
        self.assertEqual(session.commit_count, 1)

    async def test_rewind_checkpoint_supports_genesis(self) -> None:
        session = FakeSession()
        service = IndexerService(
            session=session,
            indexer=FakeIndexer(),
        )

        await service.rewind_checkpoint(0)

        self.assertEqual(session.checkpoint.last_processed_block, -1)
        self.assertEqual(
            session.checkpoint.last_block_hash,
            "before-genesis",
        )
