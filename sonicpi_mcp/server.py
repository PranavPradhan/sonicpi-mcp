"""MCP server implementation."""

import json
import os
import re
import socket
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .ai_generator import MusicAI
from .config import Config, discover_sonic_pi_port, load_config
# Inline logging and diagnostics functionality
from .osc_client import OscClient
from .patterns import get_pattern, list_patterns, get_pattern_description
from .schemas import (CreateAndPlayInput, CreateAndPlayResponse, CueInput, CueResponse, 
                     DiagnosticResponse, ErrorResponse, GenerateMusicInput, 
                     GenerateMusicResponse, GetPatternInput, GetPatternResponse, 
                     ListPatternsResponse, LogEntry, RunCodeInput, RunCodeResponse, 
                     SetBpmInput, SetBpmResponse, TailLogsInput, TailLogsResponse)


# Inline logging functionality
@dataclass
class LogRecord:
    """Internal log record structure."""
    ts: float
    level: str
    message: str


class RingLogger:
    """Ring buffer logger that maintains a fixed number of recent log entries."""
    
    def __init__(self, max_entries: int = 1000):
        """Initialize the logger with a maximum number of entries."""
        self.buffer: Deque[LogRecord] = deque(maxlen=max_entries)
    
    def log(self, level: str, message: str) -> None:
        """Add a new log entry."""
        self.buffer.append(LogRecord(
            ts=time.time() * 1000,  # Convert to milliseconds
            level=level,
            message=message
        ))
    
    def get_entries(self, since_ms: Optional[float] = None) -> List[LogEntry]:
        """Retrieve log entries, optionally filtered by timestamp."""
        entries = []
        
        for record in self.buffer:
            if since_ms is None or record.ts > since_ms:
                entries.append(LogEntry(
                    ts=record.ts,
                    level=record.level,
                    message=record.message
                ))
        
        return entries


# Global logger instance
logger = RingLogger()


# Inline diagnostics functionality
def get_diagnostic_info() -> Dict[str, any]:
    """Gather all diagnostic information."""
    # Default Sonic Pi port
    default_port = 4557
    
    # Try to get port from environment
    env_port = os.getenv("SONICPI_OSC_PORT")
    if env_port:
        try:
            default_port = int(env_port)
        except ValueError:
            pass
    
    # Try to find the command port
    command_port = find_sonic_pi_command_port()
    
    return {
        "logs": find_sonic_pi_logs(),
        "port_status": check_port_status("127.0.0.1", default_port),
        "osc_test": test_osc_connection("127.0.0.1", default_port),
        "command_port": command_port,
        "command_port_status": check_port_status("127.0.0.1", command_port) if command_port else None,
        "environment": {
            "SONICPI_OSC_HOST": os.getenv("SONICPI_OSC_HOST", "127.0.0.1"),
            "SONICPI_OSC_PORT": os.getenv("SONICPI_OSC_PORT", str(default_port))
        }
    }


def find_sonic_pi_logs() -> List[Dict[str, str]]:
    """Find all potential Sonic Pi log files."""
    from pathlib import Path
    possible_paths = [
        Path.home() / ".sonic-pi/log/server-output.log",  # Unix-like
        Path.home() / "Library/Application Support/Sonic Pi/log/server-output.log",  # macOS
        Path.home() / "AppData/Local/sonic-pi/log/server-output.log",  # Windows
    ]
    
    found_logs = []
    for path in possible_paths:
        if path.exists():
            try:
                # Get last modification time and size
                stats = path.stat()
                found_logs.append({
                    "path": str(path),
                    "size": str(stats.st_size),
                    "modified": time.ctime(stats.st_mtime),
                    "active": stats.st_mtime > time.time() - 300  # Modified in last 5 minutes?
                })
            except OSError:
                continue
    
    return found_logs


def check_port_status(host: str, port: int) -> Dict[str, bool]:
    """Check if a port is open and responding."""
    try:
        # Try to create a socket connection
        with socket.create_connection((host, port), timeout=1):
            return {"open": True, "error": None}
    except socket.timeout:
        return {"open": False, "error": "Connection timed out"}
    except ConnectionRefusedError:
        return {"open": False, "error": "Connection refused"}
    except Exception as e:
        return {"open": False, "error": str(e)}


def test_osc_connection(host: str, port: int) -> Dict[str, bool]:
    """Test OSC connection by sending a simple message."""
    try:
        from pythonosc.udp_client import SimpleUDPClient
        client = SimpleUDPClient(host, port)
        # Send a cue message as a test
        client.send_message("/cue", ["test_connection"])
        return {"sent": True, "error": None}
    except Exception as e:
        return {"sent": False, "error": str(e)}


def find_sonic_pi_command_port() -> Optional[int]:
    """Try to find Sonic Pi's dynamic command port by checking running processes."""
    try:
        # Check if Sonic Pi is running and what ports it's using
        result = subprocess.run(
            ["lsof", "-i", "-P", "-n"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        # Look for Sonic Pi processes listening on ports
        command_port = None
        for line in result.stdout.split('\n'):
            if 'sonic' in line.lower() and 'LISTEN' in line:
                # Extract port number from the line
                match = re.search(r':(\d+)\s+\(LISTEN\)', line)
                if match:
                    port = int(match.group(1))
                    # Skip the standard cue port (4560) and look for command port
                    if port != 4560:
                        command_port = port
                        break
        
        return command_port
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return None

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
    
    def _reply_jsonrpc(self, request_id: Optional[int], result: Any) -> None:
        """Send a JSON-RPC 2.0 result response."""
        if request_id is None:
            return
        envelope = {"jsonrpc": "2.0", "id": request_id, "result": result}
        print(json.dumps(envelope))
        sys.stdout.flush()
    
    def _handle_error(self, code: str, message: str, request_id: Optional[int] = None) -> None:
        """Handle an error by sending an error response."""
        if hasattr(self, '_current_request_id') and self._current_request_id is not None:
            request_id = self._current_request_id
        
        # Convert string codes to numeric codes for JSON-RPC compliance
        numeric_code = -32000  # Generic server error
        if code == "UNKNOWN_METHOD":
            numeric_code = -32601
        elif code == "INVALID_JSON":
            numeric_code = -32700
        elif code == "INVALID_FORMAT":
            numeric_code = -32602
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": numeric_code,
                "message": message
            }
        }
        
        print(json.dumps(response))
        sys.stdout.flush()
    
    def run_code(self, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle run_code tool invocation."""
        try:
            input_data = self._parse_input(args, RunCodeInput)
            start_time = time.time()
            job_id = self.osc.run_code(input_data.source)
            elapsed_ms = (time.time() - start_time) * 1000
            
            payload = RunCodeResponse(
                job_id=job_id,
                elapsed_ms=elapsed_ms
            ).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("RUN_CODE_ERROR", str(e), request_id)
    
    def stop_all(self, _args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle stop_all tool invocation."""
        try:
            self.osc.stop_all()
            self._reply_jsonrpc(request_id, {"ok": True})
            
        except Exception as e:
            self._handle_error("STOP_ALL_ERROR", str(e), request_id)
    
    def set_bpm(self, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle set_bpm tool invocation."""
        try:
            input_data = self._parse_input(args, SetBpmInput)
            self.osc.set_bpm(input_data.bpm)
            
            payload = SetBpmResponse(bpm=input_data.bpm).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("SET_BPM_ERROR", str(e), request_id)
    
    def cue(self, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle cue tool invocation."""
        try:
            input_data = self._parse_input(args, CueInput)
            self.osc.cue(input_data.tag)
            
            payload = CueResponse(tag=input_data.tag).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("CUE_ERROR", str(e), request_id)
    
    def tail_logs(self, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle tail_logs tool invocation."""
        try:
            input_data = self._parse_input(args, TailLogsInput)
            entries = logger.get_entries(input_data.since_ms)
            
            payload = TailLogsResponse(entries=entries).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("TAIL_LOGS_ERROR", str(e), request_id)
    
    def diagnose(self, _args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle diagnostic tool invocation."""
        try:
            info = get_diagnostic_info()
            payload = DiagnosticResponse(**info).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("DIAGNOSTIC_ERROR", str(e), request_id)
    
    def generate_music(self, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle generate_music tool invocation."""
        try:
            input_data = self._parse_input(args, GenerateMusicInput)
            code, method_used = self.music_ai.generate_music_code(input_data.request)
            suggestions = self.music_ai.suggest_improvements(input_data.request)
            
            payload = GenerateMusicResponse(
                code=code,
                method_used=method_used,
                suggestions=suggestions
            ).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("GENERATE_MUSIC_ERROR", str(e), request_id)
    
    def list_patterns(self, _args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle list_patterns tool invocation."""
        try:
            patterns = list_patterns()
            payload = ListPatternsResponse(patterns=patterns).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("LIST_PATTERNS_ERROR", str(e), request_id)
    
    def get_pattern(self, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
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
                    f"Pattern '{input_data.pattern_name}' not found in category '{input_data.category}'",
                    request_id
                )
                return
            
            description = get_pattern_description(input_data.category, input_data.pattern_name)
            
            payload = GetPatternResponse(
                code=code,
                description=description or "No description available"
            ).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("GET_PATTERN_ERROR", str(e), request_id)
    
    def create_and_play(self, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
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
            
            payload = CreateAndPlayResponse(
                code=code,
                method_used=method_used,
                job_id=job_id,
                elapsed_ms=elapsed_ms,
                suggestions=suggestions
            ).model_dump()
            self._reply_jsonrpc(request_id, payload)
            
        except Exception as e:
            self._handle_error("CREATE_AND_PLAY_ERROR", str(e), request_id)
    
    def run(self) -> None:
        """Run the MCP server, processing stdin commands."""
        # Remove the invalid "ready" message - MCP clients expect initialize first
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                command = json.loads(line)
                
                # Handle MCP protocol messages
                if "method" in command:
                    self._handle_mcp_message(command)
                # Handle legacy tool format
                elif "tool" in command:
                    tool = command.get("tool")
                    args = command.get("args", {})
                    self._handle_tool_call(tool, args)
                else:
                    self._handle_error(
                        "INVALID_FORMAT",
                        "Expected 'method' or 'tool' field"
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
    
    def _handle_mcp_message(self, command: Dict[str, Any]) -> None:
        """Handle MCP protocol messages."""
        method = command.get("method")
        params = command.get("params", {})
        request_id = command.get("id")
        
        if method == "initialize":
            self._reply_jsonrpc(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "sonicpi",
                    "version": "0.1.0"
                }
            })
        elif method == "tools/list":
            self._list_tools(request_id)
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            self._handle_tool_call(tool_name, tool_args, request_id)
        else:
            self._handle_error(
                "UNKNOWN_METHOD",
                f"Unknown method: {method}",
                request_id
            )
    
    def _list_tools(self, request_id: Optional[int] = None) -> None:
        """List available tools."""
        tools = [
            {
                "name": "run_code",
                "description": "Run Sonic Pi code",
                "inputSchema": {
                    "type": "object",
                    "required": ["source"],
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Sonic Pi source code to execute"
                        }
                    }
                }
            },
            {
                "name": "stop_all",
                "description": "Stop all running jobs",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "set_bpm",
                "description": "Set the global BPM",
                "inputSchema": {
                    "type": "object",
                    "required": ["bpm"],
                    "properties": {
                        "bpm": {
                            "type": "number",
                            "description": "Beats per minute",
                            "minimum": 1
                        }
                    }
                }
            },
            {
                "name": "cue",
                "description": "Send a cue message",
                "inputSchema": {
                    "type": "object",
                    "required": ["tag"],
                    "properties": {
                        "tag": {
                            "type": "string",
                            "description": "Cue tag to trigger"
                        }
                    }
                }
            },
            {
                "name": "tail_logs",
                "description": "Get recent log entries",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "since_ms": {
                            "type": "number",
                            "description": "Only return logs after this timestamp"
                        }
                    }
                }
            },
            {
                "name": "diagnose",
                "description": "Run diagnostics to check Sonic Pi connection",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "generate_music",
                "description": "Generate Sonic Pi code from natural language description",
                "inputSchema": {
                    "type": "object",
                    "required": ["request"],
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "Natural language description of desired music (e.g., 'create a rock drum beat')"
                        }
                    }
                }
            },
            {
                "name": "list_patterns",
                "description": "List all available music patterns",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_pattern",
                "description": "Get a specific music pattern",
                "inputSchema": {
                    "type": "object",
                    "required": ["category", "pattern_name"],
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Pattern category (drums, bass, chords)"
                        },
                        "pattern_name": {
                            "type": "string",
                            "description": "Name of the pattern"
                        },
                        "bpm": {
                            "type": "number",
                            "description": "Optional BPM override"
                        }
                    }
                }
            },
            {
                "name": "create_and_play",
                "description": "Generate music from natural language and immediately play it",
                "inputSchema": {
                    "type": "object",
                    "required": ["request"],
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "Natural language description of desired music (e.g., 'create a rock drum beat and play it')"
                        }
                    }
                }
            }
        ]
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
        print(json.dumps(response))
        sys.stdout.flush()
    
    def _handle_tool_call(self, tool_name: str, args: Dict[str, Any], request_id: Optional[int] = None) -> None:
        """Handle tool invocation."""
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
        
        handler = handlers.get(tool_name)
        if handler:
            # Store request_id for response formatting
            self._current_request_id = request_id
            handler(args, request_id)  # Pass request_id to all handlers
        else:
            self._handle_error(
                "UNKNOWN_TOOL",
                f"Unknown tool: {tool_name}",
                request_id
            )
