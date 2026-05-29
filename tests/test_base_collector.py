import json
import pytest
from unittest.mock import MagicMock, patch
from src.ingestion.base_collector import BaseCollector


class ConcreteCollector(BaseCollector):
    """
    Implémentation minimale de BaseCollector pour les tests.
    On ne teste pas une classe abstraite directement.
    """
    def collect(self) -> int:
        return 0


@pytest.fixture
def collector():
    """
    Fixture : instancie ConcreteCollector avec une connexion BDD mockée.
    Aucune vraie connexion PostgreSQL n'est établie pendant les tests.
    """
    with patch("src.ingestion.base_collector.psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        c = ConcreteCollector(source_name="test_source")
        yield c


class TestGenerateHash:

    def test_is_deterministic(self, collector):
        """Même input produit toujours le même hash."""
        data = {"titre": "Data Engineer", "lieu": "Paris"}
        assert collector._generate_hash(data) == collector._generate_hash(data)

    def test_sort_keys_has_no_impact(self, collector):
        """L'ordre des clés ne change pas le hash."""
        data_a = {"titre": "Data Engineer", "lieu": "Paris"}
        data_b = {"lieu": "Paris", "titre": "Data Engineer"}
        assert collector._generate_hash(data_a) == collector._generate_hash(data_b)

    def test_different_data_produces_different_hash(self, collector):
        """Des données différentes produisent des hashs différents."""
        data_a = {"titre": "Data Engineer"}
        data_b = {"titre": "Data Analyst"}
        assert collector._generate_hash(data_a) != collector._generate_hash(data_b)


class TestSaveRaw:

    def test_inserts_new_offer(self, collector):
        """Une nouvelle offre est insérée — retourne True."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        collector.conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        collector.conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = collector._save_raw({"titre": "Data Engineer"})
        assert result is True

    def test_ignores_duplicate(self, collector):
        """Un doublon est ignoré silencieusement — retourne False."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        collector.conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        collector.conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = collector._save_raw({"titre": "Data Engineer"})
        assert result is False
