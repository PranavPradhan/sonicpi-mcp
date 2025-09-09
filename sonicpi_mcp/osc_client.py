"""OSC client for communicating with Sonic Pi."""

import re
import subprocess
import time
import uuid
from typing import Optional

from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_message_builder import OscMessageBuilder

from .config import OscConfig


class OscClient:
    """Client for sending OSC messages to Sonic Pi."""
    
    def __init__(self, config: OscConfig):
        """Initialize the OSC client with configuration."""
        self.config = config
        self._client = None
        self._last_discovered_port = None
        self._init_client()
        
    def _discover_sonic_pi_port(self) -> Optional[int]:
        """Discover Sonic Pi's current command port."""
        try:
            result = subprocess.run(
                ["lsof", "-i", "-P", "-n"], 
                capture_output=True, 
                text=True, 
                timeout=3
            )
            
            for line in result.stdout.split('\n'):
                if 'sonic' in line.lower() and 'UDP' in line and '127.0.0.1:' in line:
                    # Extract port number
                    match = re.search(r'127\.0\.0\.1:(\d+)', line)
                    if match:
                        port = int(match.group(1))
                        print(f"INFO: Discovered Sonic Pi port: {port}")
                        return port
            
            print("WARNING: Could not discover Sonic Pi port")
            return None
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: Failed to discover Sonic Pi port")
            return None
    
    def _init_client(self):
        """Initialize or reinitialize the UDP client."""
        # Try to discover the port if not manually set
        discovered_port = self._discover_sonic_pi_port()
        
        if discovered_port and discovered_port != self._last_discovered_port:
            self.config.port = discovered_port
            self._last_discovered_port = discovered_port
            print(f"INFO: Using discovered port: {discovered_port}")
        
        self._client = SimpleUDPClient(self.config.host, self.config.port)
        print(f"INFO: OSC client initialized - {self.config.host}:{self.config.port}")
    
    def send_message(self, address: str, *args) -> None:
        """Send an OSC message to the specified address."""
        try:
            # Rediscover port if connection seems to fail
            if not self._client:
                self._init_client()
            
            # Build message with explicit types
            builder = OscMessageBuilder(address=address)
            for arg in args:
                if isinstance(arg, str):
                    builder.add_arg(arg, 's')
                elif isinstance(arg, int):
                    builder.add_arg(arg, 'i')
                elif isinstance(arg, float):
                    builder.add_arg(arg, 'f')
                else:
                    builder.add_arg(arg)
            msg = builder.build()
            self._client.send(msg)
            print(f"DEBUG: Sent OSC message {address} to {self.config.host}:{self.config.port}")
        except Exception as e:
            print(f"ERROR: Failed to send OSC message to {address}: {e}")
            # Try to rediscover port and retry once
            self._init_client()
            raise
    
    def run_code(self, source: str) -> str:
        """Send code to Sonic Pi for execution."""
        job_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Format the code with proper line endings
            formatted_source = source.strip()
            
            # Send to the cue port (4560) which Sonic Pi definitely listens to
            cue_client = SimpleUDPClient("192.168.2.62", 4560)
            
            # Send as a cue message that can be received by sync in Sonic Pi
            cue_builder = OscMessageBuilder(address="/mcp/code")
            cue_builder.add_arg(formatted_source, 's')
            cue_msg = cue_builder.build()
            cue_client.send(cue_msg)
            
            print(f"INFO: Sent code to Sonic Pi via /mcp/code (job {job_id})")
            return job_id
        except Exception as e:
            print(f"ERROR: Failed to run code: {e}")
            raise
        finally:
            elapsed = (time.time() - start_time) * 1000
            print(f"INFO: Code execution took {elapsed:.2f}ms")
    
    def stop_all(self) -> None:
        """Stop all running jobs."""
        try:
            self.send_message(self.config.stop_all_path)
            print("INFO: Sent stop-all command")
        except Exception as e:
            print(f"ERROR: Failed to stop all jobs: {e}")
            raise
    
    def set_bpm(self, bpm: float) -> None:
        """Set the global BPM."""
        try:
            self.send_message(self.config.set_bpm_path, bpm)
            print(f"INFO: Set BPM to {bpm}")
        except Exception as e:
            print(f"ERROR: Failed to set BPM: {e}")
            raise
    
    def cue(self, tag: str) -> None:
        """Send a cue message."""
        try:
            self.send_message(self.config.cue_path, tag)
            print(f"INFO: Sent cue: {tag}")
        except Exception as e:
            print(f"ERROR: Failed to send cue: {e}")
            raise
