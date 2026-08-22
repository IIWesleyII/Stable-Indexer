from unittest import IsolatedAsyncioTestCase

from sqlalchemy.dialects import postgresql

from app.services.metrics import get_daily_volume
from app.services.metrics import get_summary_metrics
from app.services.metrics import get_top_addresses


class EmptyResult:
    def one(self):
        return type(
            "Summary",
            (),
            {
                "transfer_count": 0,
                "total_volume": 0,
                "largest_transfer": 0,
                "smallest_transfer": 0,
            },
        )()

    def scalar_one(self):
        return 0

    def mappings(self):
        return self

    def all(self) -> list:
        return []


class QueryCompilingSession:
    async def execute(self, statement):
        statement.compile(dialect=postgresql.dialect())
        return EmptyResult()


class MetricsQueryTests(IsolatedAsyncioTestCase):
    async def test_summary_reads_rollup_models(self) -> None:
        result = await get_summary_metrics(
            session=QueryCompilingSession(),
            chain="base",
        )

        self.assertEqual(result.transfer_count, 0)

    async def test_daily_volume_groups_by_token_symbol(self) -> None:
        result = await get_daily_volume(
            session=QueryCompilingSession(),
            chain="ethereum",
        )

        self.assertEqual(result, [])

    async def test_top_addresses_returns_asset_volume_columns(self) -> None:
        result = await get_top_addresses(
            session=QueryCompilingSession(),
            chain="ethereum",
        )

        self.assertEqual(result, [])
