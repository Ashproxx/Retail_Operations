"""Dataset contracts only; CSV/XLSX mapping requires the real source columns."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from pydantic import Field
from app.api.schemas import Contract
from app.core.exceptions import DataValidationError, NotFoundError


class LoadReport(Contract):
    source_name: str
    rows_seen: int = Field(ge=0)
    rows_loaded: int = Field(ge=0)
    errors: list[str] = Field(default_factory=list)
    column_mapping: dict[str, str] = Field(default_factory=dict)


class DatasetLoader(ABC):
    @staticmethod
    def validate_source(path: Path) -> Path:
        if path.suffix.lower() not in {".csv", ".xlsx"}:
            raise DataValidationError("Only CSV and XLSX sources are supported.")
        if not path.is_file():
            raise NotFoundError("Dataset file not found.")
        return path

    @abstractmethod
    def load(self, path: Path, column_mapping: dict[str, str]) -> LoadReport:
        """Validate dates/numbers/duplicates/nulls/stock and identifiers atomically."""
        raise NotImplementedError


class RetailRepository(ABC):
    @abstractmethod
    def get_current_stock(self, store_id: str, sku_id: str) -> dict[str, Any] | None:
        """Return observed stock or None, never synthetic operational values."""
        raise NotImplementedError

    @abstractmethod
    def get_store_inventory(self, store_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError
