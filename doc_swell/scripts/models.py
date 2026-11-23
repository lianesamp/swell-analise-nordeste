"""
Pydantic models for the Ceará Swell Climatology Pipeline.

Pydantic is a data-validation library that uses Python type hints to
validate data at runtime.  Think of it as Zod (from the TypeScript/React
world) but for Python: you declare a schema with types and constraints,
and Pydantic guarantees the data matches — or raises a clear error.

Why Pydantic instead of plain dicts?
  - A typo like `height_min: "1.0"` (string) is caught instantly.
  - IDE autocomplete works on model fields.
  - You get free serialization (to dict, JSON) for logging or APIs.

Alternative: dataclasses + manual validation.  Pydantic is preferred
because validation rules (ranges, types) are declarative, not imperative.
"""

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Small, reusable models
# ---------------------------------------------------------------------------

class GeoPoint(BaseModel):
    """A geographic coordinate with latitude and longitude validation."""

    lat: float = Field(ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(ge=-180, le=180, description="Longitude in degrees")


class Scenario(BaseModel):
    """
    One surf-quality scenario (e.g. 'good', 'exceptional').

    Each scenario is defined by minimum period and height thresholds.
    If swell meets both thresholds simultaneously, we count it as an event.
    """

    name: str = Field(min_length=1, description="Internal identifier (e.g. 'good')")
    label: str = Field(min_length=1, description="Human-readable label")
    period_min: float = Field(ge=0, description="Minimum swell period in seconds")
    height_min: float = Field(ge=0, description="Minimum swell height in meters")


class DirectionRange(BaseModel):
    """
    A compass direction defined by one or more angular ranges.

    Directions use the FROM convention: 0 = from North, 90 = from East.
    North wraps around 360, so 'N' needs two ranges: (337.5–360) and (0–22.5).
    """

    name: str = Field(min_length=1)
    ranges: list[tuple[float, float]]

    @field_validator("ranges")
    @classmethod
    def validate_ranges(cls, v: list[tuple[float, float]]) -> list[tuple[float, float]]:
        """
        field_validator is a Pydantic decorator that runs custom validation
        on a single field.  The @classmethod is required by Pydantic v2.

        Similar to Laravel's custom validation rules, but declared inline.
        """
        for start, end in v:
            if not (0 <= start <= 360 and 0 <= end <= 360):
                raise ValueError(
                    f"Direction range ({start}, {end}) must be within 0–360 degrees"
                )
            if start > end:
                raise ValueError(
                    f"Direction range start ({start}) must be <= end ({end}). "
                    "For wrap-around (e.g. North), use two separate ranges."
                )
        return v


class MarchWindow(BaseModel):
    """A week-window within March for analysis (e.g. week 3 = days 15–21)."""

    name: str = Field(min_length=1)
    start_day: int = Field(ge=1, le=31)
    end_day: int = Field(ge=1, le=31)
    label: str = Field(min_length=1)

    @model_validator(mode="after")
    def end_after_start(self) -> "MarchWindow":
        """
        model_validator runs after ALL fields are set, so it can compare
        multiple fields.  Similar to Zod's .refine() in TypeScript.
        """
        if self.end_day < self.start_day:
            raise ValueError(
                f"end_day ({self.end_day}) must be >= start_day ({self.start_day})"
            )
        return self


class VariableMapping(BaseModel):
    """Maps generic names (height, direction, period) to dataset-specific names."""

    height: str = Field(min_length=1)
    direction: str = Field(min_length=1)
    period: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Top-level pipeline configuration
# ---------------------------------------------------------------------------

class PipelineConfig(BaseModel):
    """
    The complete, validated configuration for the swell pipeline.

    This model wraps everything from config.py into a single validated
    object.  If ANY value is wrong (bad type, out of range, missing),
    Pydantic raises a ValidationError with a clear message — before
    the pipeline even starts running.

    Usage:
        from models import PipelineConfig
        from config import get_validated_config

        cfg = get_validated_config()  # returns PipelineConfig
        print(cfg.geo_point.lat)      # -3.5
        print(cfg.scenarios_era5[2].name)  # 'good'
    """

    # Geographic point
    geo_point: GeoPoint

    # Year ranges
    era5_year_start: int = Field(ge=1900, le=2100)
    era5_year_end: int = Field(ge=1900, le=2100)
    ww3_year_start: int = Field(ge=1900, le=2100)
    ww3_year_end: int = Field(ge=1900, le=2100)

    # Scenario definitions
    scenarios_era5: list[Scenario] = Field(min_length=1)
    scenarios_ww3: list[Scenario] = Field(min_length=1)

    # Direction definitions
    directions: list[DirectionRange] = Field(min_length=1)
    default_direction: str = Field(min_length=1)

    # March windows
    march_windows: list[MarchWindow] = Field(min_length=1)

    # Variable mappings
    era5_vars: VariableMapping
    ww3_vars: VariableMapping

    # Event detection
    gap_tolerance_hours: int = Field(ge=0)

    # Distribution bins
    height_bins: list[float] = Field(min_length=2)
    height_labels: list[str] = Field(min_length=1)
    period_bins: list[float] = Field(min_length=2)
    period_labels: list[str] = Field(min_length=1)

    # Window durations
    window_durations: list[int] = Field(min_length=1)

    # Paths (strings — we validate they're non-empty, not that dirs exist,
    # because the pipeline creates directories as needed)
    base_dir: str = Field(min_length=1)
    era5_nc_dir: str = Field(min_length=1)
    output_dir: str = Field(min_length=1)
    data_dir: str = Field(min_length=1)

    @model_validator(mode="after")
    def year_ranges_valid(self) -> "PipelineConfig":
        """Ensure start years come before end years."""
        if self.era5_year_end < self.era5_year_start:
            raise ValueError(
                f"ERA5 year range invalid: {self.era5_year_start}–{self.era5_year_end}"
            )
        if self.ww3_year_end < self.ww3_year_start:
            raise ValueError(
                f"WW3 year range invalid: {self.ww3_year_start}–{self.ww3_year_end}"
            )
        return self

    @model_validator(mode="after")
    def bins_match_labels(self) -> "PipelineConfig":
        """Bins arrays should have exactly one more element than labels."""
        if len(self.height_bins) != len(self.height_labels) + 1:
            raise ValueError(
                f"height_bins ({len(self.height_bins)}) must have exactly "
                f"one more element than height_labels ({len(self.height_labels)})"
            )
        if len(self.period_bins) != len(self.period_labels) + 1:
            raise ValueError(
                f"period_bins ({len(self.period_bins)}) must have exactly "
                f"one more element than period_labels ({len(self.period_labels)})"
            )
        return self

    @model_validator(mode="after")
    def default_direction_exists(self) -> "PipelineConfig":
        """The default direction must be one of the defined directions."""
        names = {d.name for d in self.directions}
        if self.default_direction not in names:
            raise ValueError(
                f"default_direction '{self.default_direction}' not found "
                f"in defined directions: {names}"
            )
        return self
