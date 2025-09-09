"""Configuration management for the MCP server."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class OscConfig(BaseModel):
    """OSC-related configuration."""
    host: str = Field(default="127.0.0.1", description="OSC server host")
    port: int = Field(default=4557, description="OSC server port")
    
    # Default OSC paths - these match Sonic Pi's defaults
    run_code_path: str = Field(default="/save-and-run-buffer", description="OSC path for run_code")
    stop_all_path: str = Field(default="/stop-all-jobs", description="OSC path for stop_all")
    set_bpm_path: str = Field(default="/bpm", description="OSC path for set_bpm")
    cue_path: str = Field(default="/sync", description="OSC path for cue")


class LogConfig(BaseModel):
    """Logging configuration."""
    max_entries: int = Field(default=1000, description="Maximum number of log entries to keep")
    level: str = Field(default="INFO", description="Minimum log level to record")


class Config(BaseModel):
    """Main configuration object."""
    osc: OscConfig = Field(default_factory=OscConfig)
    logging: LogConfig = Field(default_factory=LogConfig)


def load_config() -> Config:
    """Load configuration from environment variables and/or config file."""
    load_dotenv()
    
    # Allow environment variables to override defaults
    osc_config = OscConfig(
        host=os.getenv("SONICPI_OSC_HOST", "127.0.0.1"),
        port=int(os.getenv("SONICPI_OSC_PORT", "4557")),
        run_code_path=os.getenv("SONICPI_OSC_RUN_PATH", "/run-code"),
        stop_all_path=os.getenv("SONICPI_OSC_STOP_PATH", "/stop-all-jobs"),
        set_bpm_path=os.getenv("SONICPI_OSC_BPM_PATH", "/bpm"),
        cue_path=os.getenv("SONICPI_OSC_CUE_PATH", "/cue")
    )
    
    log_config = LogConfig(
        max_entries=int(os.getenv("SONICPI_LOG_MAX_ENTRIES", "1000")),
        level=os.getenv("SONICPI_LOG_LEVEL", "INFO")
    )
    
    return Config(osc=osc_config, logging=log_config)


def discover_sonic_pi_port() -> Optional[int]:
    """Attempt to auto-discover Sonic Pi's OSC port from its session files."""
    # Common locations for Sonic Pi session info
    paths = [
        Path.home() / ".sonic-pi/log/server-output.log",  # Unix-like
        Path.home() / "AppData/Local/sonic-pi/log/server-output.log",  # Windows
    ]
    
    for path in paths:
        if path.exists():
            try:
                # Read the last few lines to find port info
                with open(path) as f:
                    for line in f.readlines()[-50:]:  # Check last 50 lines
                        if "Server port" in line and ":" in line:
                            port = line.split(":")[-1].strip()
                            return int(port)
            except (IOError, ValueError):
                continue
    
    return None
