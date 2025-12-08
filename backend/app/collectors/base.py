"""Base collector interface."""

from abc import ABC, abstractmethod

from app.models import Source
from app.schemas.source import SourceTestResult


class BaseCollector(ABC):
    """Abstract base class for data collectors."""

    def __init__(self, source: Source):
        """Initialize collector with source configuration."""
        self.source = source

    @abstractmethod
    async def test_connection(self) -> SourceTestResult:
        """Test the connection to the source."""
        pass

    @abstractmethod
    async def collect(self) -> None:
        """Collect data from the source."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start continuous collection (for MQTT) or schedule polling."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop collection."""
        pass
