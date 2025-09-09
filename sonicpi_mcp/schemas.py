"""Contract definitions for the MCP server tools."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, PositiveFloat, constr


class SuccessResponse(BaseModel):
    """Base success response for all tools."""
    ok: bool = True


class ErrorResponse(BaseModel):
    """Common error response shape for all tools."""
    ok: bool = False
    code: str
    message: str


class RunCodeResponse(SuccessResponse):
    """Response from run_code tool."""
    job_id: str
    elapsed_ms: float


class SetBpmResponse(SuccessResponse):
    """Response from set_bpm tool."""
    bpm: float


class CueResponse(SuccessResponse):
    """Response from cue tool."""
    tag: str


class LogEntry(BaseModel):
    """Individual log entry for tail_logs."""
    ts: float
    level: str
    message: str


class TailLogsResponse(SuccessResponse):
    """Response from tail_logs tool."""
    entries: List[LogEntry]


# Input schemas
class RunCodeInput(BaseModel):
    """Input for run_code tool."""
    source: str = Field(..., description="Sonic Pi source code to execute")


class SetBpmInput(BaseModel):
    """Input for set_bpm tool."""
    bpm: PositiveFloat = Field(..., description="Beats per minute")


class CueInput(BaseModel):
    """Input for cue tool."""
    tag: constr(min_length=1) = Field(..., description="Cue tag to trigger")


class TailLogsInput(BaseModel):
    """Input for tail_logs tool."""
    since_ms: Optional[float] = Field(None, description="Only return logs after this timestamp")


class DiagnosticResponse(SuccessResponse):
    """Response from diagnostic tool."""
    logs: List[Dict[str, str]]
    port_status: Dict[str, Any]
    osc_test: Dict[str, Any]
    command_port: Optional[int]
    command_port_status: Optional[Dict[str, Any]]
    environment: Dict[str, str]


# New AI-powered tools
class GenerateMusicInput(BaseModel):
    """Input for generate_music tool."""
    request: str = Field(..., description="Natural language description of desired music")


class GenerateMusicResponse(SuccessResponse):
    """Response from generate_music tool."""
    code: str
    method_used: str
    suggestions: List[str]


class ListPatternsResponse(SuccessResponse):
    """Response from list_patterns tool."""
    patterns: Dict[str, List[str]]


class GetPatternInput(BaseModel):
    """Input for get_pattern tool."""
    category: str = Field(..., description="Pattern category (drums, bass, chords)")
    pattern_name: str = Field(..., description="Name of the pattern")
    bpm: Optional[int] = Field(None, description="Optional BPM override")


class GetPatternResponse(SuccessResponse):
    """Response from get_pattern tool."""
    code: str
    description: str


class CreateAndPlayInput(BaseModel):
    """Input for create_and_play tool."""
    request: str = Field(..., description="Natural language description of desired music")


class CreateAndPlayResponse(SuccessResponse):
    """Response from create_and_play tool."""
    code: str
    method_used: str
    job_id: str
    elapsed_ms: float
    suggestions: List[str]
