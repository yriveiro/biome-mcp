from typing import Literal

from pydantic import BaseModel

type CheckLevel = Literal["all", "error", "warning"]
type DiagnosticLevel = Literal["error", "warning", "info"]


class BiomeError(BaseModel):
    """A single Biome lint or format finding."""

    file: str
    line: int
    col: int
    level: DiagnosticLevel
    code: str
    message: str
    fixable: bool = False


class TokenMetrics(BaseModel):
    """Estimated token savings of the compact output versus raw output."""

    raw_tokens: int
    processed_tokens: int
    saved_tokens: int
    savings_percent: int


class CheckResult(BaseModel):
    """
    Result of a Biome check run.

    Attributes:
        output: Token-efficient output for the model.
        exit_code: Exit code of the underlying command.
        issues: Number of findings (lint issues or unformatted files,
            depending on the tool).
        fixable: Number of findings with an available fix.
        warnings: Number of warning-level diagnostics.
        saved_tokens: Estimated tokens removed from the raw output.
        savings_percent: Share of raw tokens removed, rounded.
    """

    output: str
    exit_code: int
    issues: int = 0
    fixable: int = 0
    warnings: int = 0
    saved_tokens: int = 0
    savings_percent: int = 0

    @property
    def clean(self) -> bool:
        """True when the underlying command reported no findings."""
        return self.exit_code == 0
