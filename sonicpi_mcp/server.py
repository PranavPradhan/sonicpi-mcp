"""MCP server implementation."""

import json
import sys
import time
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .ai_generator import MusicAI
from .config import Config, discover_sonic_pi_port, load_config
from .diagnostics import get_diagnostic_info
from .logging import logger
from .osc_client import OscClient
from .patterns import get_pattern, list_patterns, get_pattern_description
from .schemas import (CreateAndPlayInput, CreateAndPlayResponse, CueInput, CueResponse, 
                     DiagnosticResponse, ErrorResponse, GenerateMusicInput, 
                     GenerateMusicResponse, GetPatternInput, GetPatternResponse, 
                     ListPatternsResponse, RunCodeInput, RunCodeResponse, 
                     SetBpmInput, SetBpmResponse, TailLogsInput, TailLogsResponse)

T = TypeVar('T', bound=BaseModel)


class McpServer:
    """MCP server that handles tool invocations via stdio."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.config = load_config()
        
        # Try to auto-discover Sonic Pi port
        discovered_port = discover_sonic_pi_port()
        if discovered_port:
            self.config.osc.port = discovered_port
            logger.log("INFO", f"Auto-discovered Sonic Pi port: {discovered_port}")
        
        self.osc = OscClient(self.config.osc)
        self.music_ai = MusicAI()
        logger.log("INFO", "MCP server initialized with AI capabilities")
    
    def _parse_input(self, data: Dict[str, Any], model: Type[T]) -> T:
        """Parse and validate input against a schema."""
        try:
            return model.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e}")
    
    def _handle_error(self, code: str, message: str) -> None:
        """Handle an error by sending an error response."""
        response = ErrorResponse(code=code, message=message)
        print(response.model_dump_json())
        sys.stdout.flush()
    
    def run_code(self, args: Dict[str, Any]) -> None:
        """Handle run_code tool invocation."""
        try:
            input_data = self._parse_input(args, RunCodeInput)
            start_time = time.time()
            job_id = self.osc.run_code(input_data.source)
            elapsed_ms = (time.time() - start_time) * 1000
            
            response = RunCodeResponse(
                job_id=job_id,
                elapsed_ms=elapsed_ms
            )
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("RUN_CODE_ERROR", str(e))
    
    def stop_all(self, _args: Dict[str, Any]) -> None:
        """Handle stop_all tool invocation."""
        try:
            self.osc.stop_all()
            print(json.dumps({"ok": True}))
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("STOP_ALL_ERROR", str(e))
    
    def set_bpm(self, args: Dict[str, Any]) -> None:
        """Handle set_bpm tool invocation."""
        try:
            input_data = self._parse_input(args, SetBpmInput)
            self.osc.set_bpm(input_data.bpm)
            
            response = SetBpmResponse(bpm=input_data.bpm)
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("SET_BPM_ERROR", str(e))
    
    def cue(self, args: Dict[str, Any]) -> None:
        """Handle cue tool invocation."""
        try:
            input_data = self._parse_input(args, CueInput)
            self.osc.cue(input_data.tag)
            
            response = CueResponse(tag=input_data.tag)
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("CUE_ERROR", str(e))
    
    def tail_logs(self, args: Dict[str, Any]) -> None:
        """Handle tail_logs tool invocation."""
        try:
            input_data = self._parse_input(args, TailLogsInput)
            entries = logger.get_entries(input_data.since_ms)
            
            response = TailLogsResponse(entries=entries)
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("TAIL_LOGS_ERROR", str(e))
    
    def diagnose(self, _args: Dict[str, Any]) -> None:
        """Handle diagnostic tool invocation."""
        try:
            info = get_diagnostic_info()
            response = DiagnosticResponse(**info)
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("DIAGNOSTIC_ERROR", str(e))
    
    def generate_music(self, args: Dict[str, Any]) -> None:
        """Handle generate_music tool invocation."""
        try:
            input_data = self._parse_input(args, GenerateMusicInput)
            code, method_used = self.music_ai.generate_music_code(input_data.request)
            suggestions = self.music_ai.suggest_improvements(input_data.request)
            
            response = GenerateMusicResponse(
                code=code,
                method_used=method_used,
                suggestions=suggestions
            )
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("GENERATE_MUSIC_ERROR", str(e))
    
    def list_patterns(self, _args: Dict[str, Any]) -> None:
        """Handle list_patterns tool invocation."""
        try:
            patterns = list_patterns()
            response = ListPatternsResponse(patterns=patterns)
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("LIST_PATTERNS_ERROR", str(e))
    
    def get_pattern(self, args: Dict[str, Any]) -> None:
        """Handle get_pattern tool invocation."""
        try:
            input_data = self._parse_input(args, GetPatternInput)
            code = get_pattern(
                input_data.category, 
                input_data.pattern_name,
                bpm=input_data.bpm or 120
            )
            
            if not code:
                self._handle_error(
                    "PATTERN_NOT_FOUND",
                    f"Pattern '{input_data.pattern_name}' not found in category '{input_data.category}'"
                )
                return
            
            description = get_pattern_description(input_data.category, input_data.pattern_name)
            
            response = GetPatternResponse(
                code=code,
                description=description or "No description available"
            )
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("GET_PATTERN_ERROR", str(e))
    
    def create_and_play(self, args: Dict[str, Any]) -> None:
        """Handle create_and_play tool invocation - generates and immediately plays music."""
        try:
            input_data = self._parse_input(args, CreateAndPlayInput)
            
            # Generate the music code
            code, method_used = self.music_ai.generate_music_code(input_data.request)
            suggestions = self.music_ai.suggest_improvements(input_data.request)
            
            # Execute the code immediately
            start_time = time.time()
            job_id = self.osc.run_code(code)
            elapsed_ms = (time.time() - start_time) * 1000
            
            response = CreateAndPlayResponse(
                code=code,
                method_used=method_used,
                job_id=job_id,
                elapsed_ms=elapsed_ms,
                suggestions=suggestions
            )
            print(response.model_dump_json())
            sys.stdout.flush()
            
        except Exception as e:
            self._handle_error("CREATE_AND_PLAY_ERROR", str(e))
    
    def run(self) -> None:
        """Run the MCP server, processing stdin commands."""
        print(json.dumps({"status": "ready"}))
        sys.stdout.flush()
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                command = json.loads(line)
                tool = command.get("tool")
                args = command.get("args", {})
                
                handlers = {
                    "run_code": self.run_code,
                    "stop_all": self.stop_all,
                    "set_bpm": self.set_bpm,
                    "cue": self.cue,
                    "tail_logs": self.tail_logs,
                    "diagnose": self.diagnose,
                    "generate_music": self.generate_music,
                    "list_patterns": self.list_patterns,
                    "get_pattern": self.get_pattern,
                    "create_and_play": self.create_and_play
                }
                
                handler = handlers.get(tool)
                if handler:
                    handler(args)
                else:
                    self._handle_error(
                        "UNKNOWN_TOOL",
                        f"Unknown tool: {tool}"
                    )
                    
            except json.JSONDecodeError:
                self._handle_error(
                    "INVALID_JSON",
                    "Invalid JSON input"
                )
            except Exception as e:
                self._handle_error(
                    "INTERNAL_ERROR",
                    f"Internal error: {e}"
                )
