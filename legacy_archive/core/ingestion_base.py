"""
Ingestion Base Infrastructure

Shared infrastructure for all data ingestion scripts including:
- Checkpointing (resume after crash)
- Rate limiting (per-API)
- Data validation
- Structured logging
- Upsert logic (idempotent)
"""

import os
import sys
import json
import time
import re
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import structlog

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

logger = structlog.get_logger()


@dataclass
class IngestionCheckpoint:
    """Tracks ingestion progress for resumption."""
    source_name: str
    run_id: str
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    last_processed_id: Optional[str]
    last_processed_name: Optional[str]
    started_at: str
    updated_at: str
    status: str  # 'running', 'completed', 'failed', 'paused'
    errors: List[Dict[str, Any]]


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[Dict[str, Any]]


class RateLimiter:
    """Per-API rate limiting with configurable limits."""

    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self):
        """Wait if needed to respect rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()


class IngestionBase(ABC):
    """
    Base class for all ingestion scripts.

    Provides:
    - Checkpointing for crash recovery
    - Rate limiting
    - Data validation
    - Structured logging
    - Upsert operations
    """

    # Default rate limits per API
    RATE_LIMITS = {
        'chembl': 5.0,      # 5 requests/second
        'pubmed': 3.0,      # 3 requests/second (10 with API key)
        'openfda': 4.0,     # 240 requests/minute
        'clinicaltrials': 10.0,  # No strict limit
        'opentargets': 5.0,
        'uniprot': 5.0,
    }

    def __init__(
        self,
        source_name: str,
        checkpoint_dir: Optional[str] = None,
        rate_limit: Optional[float] = None
    ):
        self.source_name = source_name
        self.db = get_client()

        # Set up checkpoint directory
        if checkpoint_dir:
            self.checkpoint_dir = Path(checkpoint_dir)
        else:
            self.checkpoint_dir = Path(__file__).parent.parent / 'data' / 'checkpoints'
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Set up rate limiter
        rate = rate_limit or self.RATE_LIMITS.get(source_name, 1.0)
        self.rate_limiter = RateLimiter(rate)

        # Initialize checkpoint
        self.checkpoint: Optional[IngestionCheckpoint] = None
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        logger.info(
            "Ingestion initialized",
            source=source_name,
            run_id=self.run_id,
            rate_limit=rate
        )

    # ==================== CHECKPOINTING ====================

    def _checkpoint_path(self) -> Path:
        """Get path to checkpoint file."""
        return self.checkpoint_dir / f'{self.source_name}_checkpoint.json'

    def load_checkpoint(self) -> Optional[IngestionCheckpoint]:
        """Load existing checkpoint if available."""
        path = self._checkpoint_path()
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                self.checkpoint = IngestionCheckpoint(**data)
                logger.info(
                    "Loaded checkpoint",
                    source=self.source_name,
                    processed=self.checkpoint.processed_items,
                    total=self.checkpoint.total_items
                )
                return self.checkpoint
        return None

    def save_checkpoint(
        self,
        processed_items: int,
        successful_items: int,
        failed_items: int,
        last_id: Optional[str] = None,
        last_name: Optional[str] = None,
        status: str = 'running',
        errors: Optional[List[Dict[str, Any]]] = None
    ):
        """Save checkpoint for crash recovery."""
        now = datetime.now().isoformat()

        if self.checkpoint is None:
            self.checkpoint = IngestionCheckpoint(
                source_name=self.source_name,
                run_id=self.run_id,
                total_items=0,
                processed_items=0,
                successful_items=0,
                failed_items=0,
                last_processed_id=None,
                last_processed_name=None,
                started_at=now,
                updated_at=now,
                status='running',
                errors=[]
            )

        self.checkpoint.processed_items = processed_items
        self.checkpoint.successful_items = successful_items
        self.checkpoint.failed_items = failed_items
        self.checkpoint.last_processed_id = last_id
        self.checkpoint.last_processed_name = last_name
        self.checkpoint.updated_at = now
        self.checkpoint.status = status
        if errors:
            self.checkpoint.errors.extend(errors[-10:])  # Keep last 10 errors

        path = self._checkpoint_path()
        with open(path, 'w') as f:
            json.dump(asdict(self.checkpoint), f, indent=2)

    def get_resume_offset(self) -> int:
        """Get offset to resume from if checkpoint exists."""
        checkpoint = self.load_checkpoint()
        if checkpoint and checkpoint.status == 'running':
            logger.info(
                "Resuming from checkpoint",
                offset=checkpoint.processed_items
            )
            return checkpoint.processed_items
        return 0

    def clear_checkpoint(self):
        """Clear checkpoint after successful completion."""
        path = self._checkpoint_path()
        if path.exists():
            path.unlink()
            logger.info("Checkpoint cleared", source=self.source_name)

    # ==================== RATE LIMITING ====================

    def rate_limit(self):
        """Apply rate limiting before API call."""
        self.rate_limiter.wait()

    # ==================== DRUG NAME NORMALIZATION ====================

    @staticmethod
    def normalize_drug_name(name: str) -> str:
        """
        Normalize drug name for API queries.

        Removes:
        - Dosage info (100 mg, 2.5 mcg, etc.)
        - Form descriptors (tablet, capsule, injection)
        - Route info (oral, IV, topical)
        """
        if not name:
            return ""

        # Convert to lowercase for processing
        normalized = name.strip()

        # Remove dosage patterns
        dosage_patterns = [
            r'\s*\d+\.?\d*\s*(mg|mcg|g|ml|%|iu|units?|doses?)\b.*$',
            r'\s*\d+\.?\d*\s*(mg|mcg|g|ml)/\s*(m2|kg|ml|l)\b.*$',
            r'\s+\d+\s*$',  # Trailing numbers (but preserve compound IDs like VMD-928)
        ]

        for pattern in dosage_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Remove form descriptors
        form_patterns = [
            r'\b(tablet|capsule|injection|solution|suspension|cream|ointment|patch|inhaler|spray)\b',
            r'\b(oral|iv|im|sc|topical|sublingual|intramuscular|intravenous|subcutaneous)\b',
            r'\b(extended.?release|immediate.?release|sustained.?release|er|ir|sr|xl|xr|cr)\b',
        ]

        for pattern in form_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    @staticmethod
    def is_valid_drug_name(name: str) -> bool:
        """
        Check if name is likely a valid drug.

        Returns False for:
        - Placebo, control, vehicle
        - Pure numbers
        - Generic procedure names
        """
        if not name:
            return False

        name_lower = name.lower().strip()

        # Invalid patterns
        invalid_terms = [
            'placebo', 'control', 'vehicle', 'saline', 'sham',
            'standard of care', 'standard care', 'best supportive care',
            'no treatment', 'observation', 'watchful waiting',
            'gene therapy', 'cell therapy', 'radiation',
        ]

        for term in invalid_terms:
            if term in name_lower:
                return False

        # Must have at least some letters
        if not re.search(r'[a-zA-Z]', name):
            return False

        # Reject very short names (likely abbreviations)
        if len(name) < 3:
            return False

        return True

    # ==================== DATABASE OPERATIONS ====================

    def get_or_create_drug(
        self,
        name: str,
        chembl_id: Optional[str] = None,
        table: str = 'drugs'  # Use 'drugs' for neuropsych, 'drug' for general
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing drug or create new one.

        Deduplication strategy:
        1. Check by chembl_id if provided
        2. Check by exact name match
        3. Create new if not found
        """
        try:
            # Try by ChEMBL ID first
            if chembl_id:
                result = self.db.client.table(table).select('*').eq('chembl_id', chembl_id).execute()
                if result.data:
                    return result.data[0]

            # Try by name
            result = self.db.client.table(table).select('*').ilike('name', name).execute()
            if result.data:
                return result.data[0]

            # Not found
            return None

        except Exception as e:
            logger.error("Failed to get drug", name=name, error=str(e))
            return None

    def upsert_drug(
        self,
        data: Dict[str, Any],
        table: str = 'drugs'
    ) -> Optional[Dict[str, Any]]:
        """
        Insert or update drug record.

        Uses chembl_id as unique constraint if available,
        otherwise uses name.
        """
        try:
            data['updated_at'] = datetime.now().isoformat()

            # Determine conflict column
            if data.get('chembl_id'):
                result = self.db.client.table(table).upsert(
                    data,
                    on_conflict='chembl_id'
                ).execute()
            else:
                result = self.db.client.table(table).upsert(
                    data,
                    on_conflict='name'
                ).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error("Failed to upsert drug", data=data, error=str(e))
            return None

    def upsert_target(
        self,
        data: Dict[str, Any],
        table: str = 'targets'
    ) -> Optional[Dict[str, Any]]:
        """Insert or update target record."""
        try:
            data['updated_at'] = datetime.now().isoformat()

            # Use symbol as unique constraint
            result = self.db.client.table(table).upsert(
                data,
                on_conflict='symbol'
            ).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error("Failed to upsert target", data=data, error=str(e))
            return None

    def batch_upsert(
        self,
        table: str,
        records: List[Dict[str, Any]],
        conflict_column: str,
        batch_size: int = 100
    ) -> Tuple[int, int]:
        """
        Batch upsert records.

        Returns: (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            # Add timestamps
            now = datetime.now().isoformat()
            for record in batch:
                record['updated_at'] = now
                if 'created_at' not in record:
                    record['created_at'] = now

            try:
                self.db.client.table(table).upsert(
                    batch,
                    on_conflict=conflict_column
                ).execute()
                successful += len(batch)
            except Exception as e:
                logger.error(
                    "Batch upsert failed",
                    table=table,
                    batch_start=i,
                    error=str(e)
                )
                failed += len(batch)

        return successful, failed

    # ==================== VALIDATION ====================

    def validate_affinity(self, value: float, unit: str = 'nM') -> ValidationResult:
        """
        Validate affinity value is in expected range.

        Expected ranges:
        - nM: 0.001 - 100,000
        - uM: 0.000001 - 100
        - pM: 1 - 100,000,000
        """
        errors = []
        warnings = []

        if value is None:
            return ValidationResult(False, ['Affinity value is None'], [], None)

        if unit == 'nM':
            if value < 0.001:
                warnings.append(f'Affinity {value} nM is unusually potent')
            if value > 100000:
                warnings.append(f'Affinity {value} nM is unusually weak')
        elif unit == 'uM':
            if value < 0.000001:
                warnings.append(f'Affinity {value} uM is unusually potent')
            if value > 100:
                warnings.append(f'Affinity {value} uM is unusually weak')

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data={'value': value, 'unit': unit}
        )

    def validate_year(self, year: int) -> ValidationResult:
        """Validate publication year is reasonable."""
        current_year = datetime.now().year
        errors = []
        warnings = []

        if year < 1900:
            errors.append(f'Year {year} is before 1900')
        if year > current_year + 1:
            errors.append(f'Year {year} is in the future')
        if year < 1950:
            warnings.append(f'Year {year} is quite old')

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data={'year': year}
        )

    # ==================== LOGGING ====================

    def log_progress(
        self,
        index: int,
        total: int,
        item_name: str,
        status: str = 'processing'
    ):
        """Log progress in consistent format."""
        logger.info(
            f"Processing item",
            source=self.source_name,
            index=f"{index}/{total}",
            item=item_name,
            status=status,
            progress=f"{(index/total)*100:.1f}%"
        )

    def log_result(
        self,
        item_name: str,
        success: bool,
        records_created: int = 0,
        records_updated: int = 0,
        error: Optional[str] = None
    ):
        """Log result of processing an item."""
        if success:
            logger.info(
                "Item processed",
                source=self.source_name,
                item=item_name,
                created=records_created,
                updated=records_updated
            )
        else:
            logger.error(
                "Item failed",
                source=self.source_name,
                item=item_name,
                error=error
            )

    def log_summary(
        self,
        total: int,
        successful: int,
        failed: int,
        duration_seconds: float
    ):
        """Log final summary."""
        logger.info(
            "Ingestion complete",
            source=self.source_name,
            total=total,
            successful=successful,
            failed=failed,
            success_rate=f"{(successful/total)*100:.1f}%" if total > 0 else "N/A",
            duration=f"{duration_seconds:.1f}s"
        )

    # ==================== ABSTRACT METHODS ====================

    @abstractmethod
    def fetch_data(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch data from external API for a single item.

        Must be implemented by subclass.
        """
        pass

    @abstractmethod
    def process_item(self, item: Dict[str, Any]) -> Tuple[bool, int, int]:
        """
        Process a single item (drug, target, etc.).

        Must be implemented by subclass.

        Returns: (success, records_created, records_updated)
        """
        pass

    def run(self, items: List[Dict[str, Any]], resume: bool = True) -> Dict[str, Any]:
        """
        Run ingestion on list of items.

        Args:
            items: List of items to process
            resume: Whether to resume from checkpoint

        Returns:
            Summary dict with counts and errors
        """
        start_time = time.time()
        total = len(items)

        # Get resume offset
        offset = self.get_resume_offset() if resume else 0

        # Initialize checkpoint
        if self.checkpoint is None:
            self.checkpoint = IngestionCheckpoint(
                source_name=self.source_name,
                run_id=self.run_id,
                total_items=total,
                processed_items=offset,
                successful_items=0,
                failed_items=0,
                last_processed_id=None,
                last_processed_name=None,
                started_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                status='running',
                errors=[]
            )
        else:
            self.checkpoint.total_items = total

        successful = self.checkpoint.successful_items
        failed = self.checkpoint.failed_items
        errors = []

        # Process items
        for i, item in enumerate(items[offset:], start=offset + 1):
            item_name = item.get('name', str(item.get('id', i)))

            try:
                self.log_progress(i, total, item_name)

                # Apply rate limiting
                self.rate_limit()

                # Process item
                success, created, updated = self.process_item(item)

                if success:
                    successful += 1
                    self.log_result(item_name, True, created, updated)
                else:
                    failed += 1
                    self.log_result(item_name, False, error="Processing failed")

            except Exception as e:
                failed += 1
                error_info = {'item': item_name, 'error': str(e)}
                errors.append(error_info)
                self.log_result(item_name, False, error=str(e))

            # Save checkpoint periodically (every 10 items)
            if i % 10 == 0:
                self.save_checkpoint(
                    processed_items=i,
                    successful_items=successful,
                    failed_items=failed,
                    last_id=str(item.get('id', '')),
                    last_name=item_name,
                    errors=errors
                )

        # Final checkpoint
        duration = time.time() - start_time
        self.save_checkpoint(
            processed_items=total,
            successful_items=successful,
            failed_items=failed,
            status='completed'
        )

        self.log_summary(total, successful, failed, duration)

        # Clear checkpoint on success
        if failed == 0:
            self.clear_checkpoint()

        return {
            'source': self.source_name,
            'run_id': self.run_id,
            'total': total,
            'successful': successful,
            'failed': failed,
            'duration_seconds': duration,
            'errors': errors[:10]  # Return first 10 errors
        }
