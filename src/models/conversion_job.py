"""Conversion job data model with status enum and state transitions."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ConversionStatus(Enum):
    """Represents the lifecycle state of a conversion job.

    State transitions:
        PENDING -> CONVERTING, SKIPPED
        CONVERTING -> COMPLETE, ERROR, CANCELLED
        COMPLETE, ERROR, CANCELLED, SKIPPED -> (terminal states)
    """

    PENDING = "Pending"
    CONVERTING = "Converting"
    COMPLETE = "Complete"
    ERROR = "Error"
    CANCELLED = "Cancelled"
    SKIPPED = "Skipped"


# Valid state transitions map
_VALID_TRANSITIONS: dict[ConversionStatus, set[ConversionStatus]] = {
    ConversionStatus.PENDING: {ConversionStatus.CONVERTING, ConversionStatus.SKIPPED},
    ConversionStatus.CONVERTING: {
        ConversionStatus.COMPLETE,
        ConversionStatus.ERROR,
        ConversionStatus.CANCELLED,
    },
    ConversionStatus.COMPLETE: set(),
    ConversionStatus.ERROR: set(),
    ConversionStatus.CANCELLED: set(),
    ConversionStatus.SKIPPED: set(),
}

TERMINAL_STATUSES = {
    ConversionStatus.COMPLETE,
    ConversionStatus.ERROR,
    ConversionStatus.CANCELLED,
    ConversionStatus.SKIPPED,
}


@dataclass
class ConversionJob:
    """Represents a single file conversion task in the queue.

    Attributes:
        id: Unique identifier (UUID).
        source_path: Absolute path to the source .ts file.
        output_path: Computed absolute path for the output .mp4 file.
        status: Current lifecycle state.
        progress: Conversion progress percentage (0.0 – 100.0).
        error_message: Human-readable error description (set when status = ERROR).
        file_size: Source file size in bytes.
        duration: Source file duration in seconds (from ffprobe), None if probe fails.
        created_at: Timestamp when job was added to queue.
        completed_at: Timestamp when job reached terminal state.
    """

    source_path: Path
    output_path: Path
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ConversionStatus = ConversionStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    file_size: int = 0
    duration: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate and compute initial values after creation."""
        if isinstance(self.source_path, str):
            self.source_path = Path(self.source_path)
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)

        # Populate file_size from source if not set and file exists
        if self.file_size == 0 and self.source_path.exists():
            self.file_size = self.source_path.stat().st_size

    @classmethod
    def from_source(
        cls,
        source_path: Path,
        output_path: Optional[Path] = None,
    ) -> "ConversionJob":
        """Create a ConversionJob from a source .ts file path.

        Args:
            source_path: Path to the source .ts file.
            output_path: Optional custom output path. If None, uses same
                directory as source with .mp4 extension.

        Returns:
            A new ConversionJob instance.
        """
        source = Path(source_path)
        if output_path is None:
            output = source.with_suffix(".mp4")
        else:
            output = Path(output_path)

        return cls(
            source_path=source,
            output_path=output,
        )

    def set_status(self, new_status: ConversionStatus, error: Optional[str] = None) -> None:
        """Transition to a new status, enforcing valid transitions.

        Args:
            new_status: The status to transition to.
            error: Optional error message (for ERROR status).

        Raises:
            ValueError: If the transition is not valid.
        """
        valid_next = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in valid_next:
            raise ValueError(
                f"Invalid status transition: {self.status.value} -> {new_status.value}. "
                f"Valid transitions: {[s.value for s in valid_next]}"
            )
        self.status = new_status

        if new_status == ConversionStatus.ERROR and error:
            self.error_message = error

        if new_status in TERMINAL_STATUSES:
            self.completed_at = datetime.now()

        if new_status == ConversionStatus.COMPLETE:
            self.progress = 100.0

    @property
    def is_terminal(self) -> bool:
        """Check if the job is in a terminal state."""
        return self.status in TERMINAL_STATUSES

    @property
    def filename(self) -> str:
        """Return the source file's base name."""
        return self.source_path.name

    @property
    def source_directory(self) -> str:
        """Return the source file's parent directory as a string."""
        return str(self.source_path.parent)


@dataclass
class QueueSummary:
    """Immutable summary snapshot of queue state after batch completion.

    Attributes:
        total: Total jobs in the batch.
        completed: Successfully converted count.
        failed: Failed with errors count.
        cancelled: Cancelled by user count.
        skipped: Skipped due to conflict policy count.
    """

    total: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    skipped: int = 0
    pending: int = 0
