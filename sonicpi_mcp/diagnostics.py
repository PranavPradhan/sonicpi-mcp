"""Diagnostic tools for Sonic Pi MCP server."""

import os
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

from pythonosc.udp_client import SimpleUDPClient

def find_sonic_pi_logs() -> List[Dict[str, str]]:
    """Find all potential Sonic Pi log files."""
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
