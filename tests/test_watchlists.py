from unittest import IsolatedAsyncioTestCase

from sqlalchemy.dialects import postgresql

from app.services.watchlists import get_watchlist_analytics
from app.services.watchlists import normalize_address


class EmptyResult:
    def mappings(self):
        return self

    def all(self) -> list:
        return []


class QueryCompilingSession:
    async def get(self, model, watchlist_id):
        return object()

    async def execute(self, statement):
        statement.compile(dialect=postgresql.dialect())
        return EmptyResult()


class WatchlistQueryTests(IsolatedAsyncioTestCase):
    def test_preserves_tron_address_casing(self) -> None:
        self.assertEqual(
            normalize_address("  TCaseSensitiveAddress  ", "tron"),
            "TCaseSensitiveAddress",
        )

    async def test_analytics_uses_targeted_activity_queries(self) -> None:
        result = await get_watchlist_analytics(
            session=QueryCompilingSession(),
            watchlist_id=1,
        )

        self.assertEqual(result, [])
