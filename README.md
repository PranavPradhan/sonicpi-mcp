# Sonic Pi MCP Server

A local-first, contract-driven MCP server for controlling Sonic Pi. This server provides a stable set of tools for interacting with Sonic Pi via OSC, with strict schemas and error handling.

## Features

- **Local-first and privacy-preserving** - no external services required
- **Contract-first design** with stable tool names and schemas
- **Auto-discovery of Sonic Pi OSC port** - automatically finds the correct port
- **AI-powered music generation** - natural language to Sonic Pi code
- **Intelligent pattern library** - pre-built musical patterns for common genres
- **Fluid command interface** - generate and play music with simple requests
- **Configurable via environment variables**
- **Built-in logging with tail support**
- **Strict input validation and error handling**

## Prerequisites

1. Python 3.8 or later
2. Sonic Pi installed and running
3. pip (Python package manager)
4. (Optional) OpenAI API key for advanced AI music generation

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/sonicpi-mcp.git
   cd sonicpi-mcp
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Set up configuration:
   ```bash
   # Copy the example environment file
   cp .env_example .env
   
   # Edit .env with your settings (optional)
   # The server works with defaults, but you can customize OSC settings and add OpenAI API key
   ```

## Configuration

The server can be configured via environment variables:

### Core Settings
- `SONICPI_OSC_HOST` - OSC server host (default: "127.0.0.1")
- `SONICPI_OSC_PORT` - OSC server port (default: 4557, auto-discovered if possible)
- `SONICPI_OSC_RUN_PATH` - OSC path for run_code (default: "/run-code")
- `SONICPI_OSC_STOP_PATH` - OSC path for stop_all (default: "/stop-all-jobs")
- `SONICPI_OSC_BPM_PATH` - OSC path for set_bpm (default: "/bpm")
- `SONICPI_OSC_CUE_PATH` - OSC path for cue (default: "/cue")
- `SONICPI_LOG_MAX_ENTRIES` - Maximum log entries to keep (default: 1000)
- `SONICPI_LOG_LEVEL` - Minimum log level (default: "INFO")

### AI Settings (Optional)
- `OPENAI_API_KEY` - OpenAI API key for advanced AI music generation

You can set these in a `.env` file in the project root:

```bash
# Basic configuration
SONICPI_OSC_HOST=127.0.0.1
SONICPI_OSC_PORT=4560

# Optional: Enable AI-powered music generation
OPENAI_API_KEY=your-openai-api-key-here
```

## Running the Server

1. **First, ensure Sonic Pi is running and set up the OSC listener:**
   
   In Sonic Pi, add this code to any buffer and click "Run":
   ```ruby
   live_loop :mcp_listener do
     use_real_time
     code_message = sync "/osc*/mcp/code"
     begin
       eval(code_message[0])
     rescue => e
       puts "Error executing code: #{e.message}"
     end
   end
   ```
   
   **Important**: This live_loop must be running for the MCP server to execute code in Sonic Pi.

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Run the server:
   ```bash
   python -m sonicpi_mcp
   ```

The server will automatically discover Sonic Pi's OSC port and print a "ready" message when initialized.

## Quick Start with AI Music Generation

1. **Set up Sonic Pi** (see "Running the Server" section above)

2. **Start the MCP server**:
   ```bash
   python -m sonicpi_mcp
   ```

3. **Try fluid music commands**:
   ```bash
   # Generate and play a rock beat
   echo '{"tool": "create_and_play", "args": {"request": "create me a rock drum beat"}}' | python3 -m sonicpi_mcp
   
   # Complex musical request
   echo '{"tool": "create_and_play", "args": {"request": "make a fast techno beat with bass and drums at 140 BPM"}}' | python3 -m sonicpi_mcp
   
   # Jazz progression
   echo '{"tool": "create_and_play", "args": {"request": "create a chill jazz progression"}}' | python3 -m sonicpi_mcp
   ```

4. **Optional: Enable advanced AI** (requires OpenAI API key):
   ```bash
   echo "OPENAI_API_KEY=your-key-here" >> .env
   ```

## Cursor Integration

To use the server with Cursor:

1. Ensure the server is running
2. Register the MCP configuration:
   ```bash
   cursor mcp register ./mcp.json
   ```

## Available Tools

### Core Tools

#### run_code
Run Sonic Pi code
- Input: `{ "source": string }`
- Output: `{ "ok": true, "job_id": string, "elapsed_ms": number }`

#### stop_all
Stop all running jobs
- Input: `{}`
- Output: `{ "ok": true }`

#### set_bpm
Set the global BPM
- Input: `{ "bpm": number }`
- Output: `{ "ok": true, "bpm": number }`

#### cue
Send a cue message
- Input: `{ "tag": string }`
- Output: `{ "ok": true, "tag": string }`

#### tail_logs
Get recent log entries
- Input: `{ "since_ms"?: number }`
- Output: `{ "ok": true, "entries": Array<{ ts: number, level: string, message: string }> }`

### AI-Powered Music Generation Tools

#### create_and_play ⭐ **RECOMMENDED**
Generate music from natural language and immediately play it
- Input: `{ "request": string }`
- Output: `{ "ok": true, "code": string, "method_used": string, "job_id": string, "elapsed_ms": number, "suggestions": string[] }`

**Examples:**
```bash
# Rock drum beat
echo '{"tool": "create_and_play", "args": {"request": "create me a rock drum beat"}}' | python3 -m sonicpi_mcp

# Complex request
echo '{"tool": "create_and_play", "args": {"request": "make a fast techno beat with bass and drums at 140 BPM"}}' | python3 -m sonicpi_mcp

# Jazz progression
echo '{"tool": "create_and_play", "args": {"request": "create a chill jazz progression"}}' | python3 -m sonicpi_mcp
```

#### generate_music
Generate Sonic Pi code from natural language (without playing)
- Input: `{ "request": string }`
- Output: `{ "ok": true, "code": string, "method_used": string, "suggestions": string[] }`

#### list_patterns
List all available music patterns
- Input: `{}`
- Output: `{ "ok": true, "patterns": { "drums": string[], "bass": string[], "chords": string[] } }`

#### get_pattern
Get a specific music pattern
- Input: `{ "category": string, "pattern_name": string, "bpm"?: number }`
- Output: `{ "ok": true, "code": string, "description": string }`

**Available Categories:**
- **drums**: rock, techno, jazz, hip_hop
- **bass**: rock, funk
- **chords**: pop, blues

### Diagnostic Tools

#### diagnose
Run diagnostics to check Sonic Pi connection
- Input: `{}`
- Output: `{ "ok": true, "logs": object[], "port_status": object, "osc_test": object, "command_port": number, "command_port_status": object, "environment": object }`

## Error Handling

All tools return errors in this format:
```json
{
    "ok": false,
    "code": string,
    "message": string
}
```

Common error codes:
- `INVALID_JSON` - Invalid JSON input
- `INVALID_INPUT` - Input validation failed
- `RUN_CODE_ERROR` - Error running code
- `STOP_ALL_ERROR` - Error stopping jobs
- `SET_BPM_ERROR` - Error setting BPM
- `CUE_ERROR` - Error sending cue
- `TAIL_LOGS_ERROR` - Error getting logs
- `INTERNAL_ERROR` - Unexpected internal error

## Manual Testing

1. **Start Sonic Pi and verify audio works**
2. **Set up the OSC listener in Sonic Pi** (see "Running the Server" section above)
3. **Start the MCP server** - it should print "ready" and auto-discover Sonic Pi's port
4. **Test using the command line** (if Cursor registration doesn't work):

   ```bash
   # Test AI-powered music generation (RECOMMENDED)
   echo '{"tool": "create_and_play", "args": {"request": "create me a rock drum beat"}}' | python3 -m sonicpi_mcp
   
   # Test complex music generation
   echo '{"tool": "create_and_play", "args": {"request": "make a fast techno beat with bass at 140 BPM"}}' | python3 -m sonicpi_mcp
   
   # Test pattern library
   echo '{"tool": "list_patterns", "args": {}}' | python3 -m sonicpi_mcp
   echo '{"tool": "get_pattern", "args": {"category": "drums", "pattern_name": "jazz"}}' | python3 -m sonicpi_mcp

   # Test core functionality
   echo '{"tool": "run_code", "args": {"source": "use_synth :prophet\nplay 60, amp: 2, release: 1"}}' | python3 -m sonicpi_mcp
   echo '{"tool": "set_bpm", "args": {"bpm": 120}}' | python3 -m sonicpi_mcp
   echo '{"tool": "stop_all", "args": {}}' | python3 -m sonicpi_mcp
   echo '{"tool": "cue", "args": {"tag": "drop"}}' | python3 -m sonicpi_mcp

   # Check logs and diagnostics
   echo '{"tool": "tail_logs", "args": {}}' | python3 -m sonicpi_mcp
   echo '{"tool": "diagnose", "args": {}}' | python3 -m sonicpi_mcp
   ```

5. **Verify that:**
   - Audio plays when running code
   - You see OSC messages in Sonic Pi's Cues panel with `/osc:*/mcp/code` paths
   - stop_all halts audio quickly
   - Invalid inputs return proper error responses
   - The diagnostic tool shows the correct discovered port

## Troubleshooting

### No Sound is Playing

**Problem**: OSC messages appear in Sonic Pi's Cues panel but no sound is produced.

**Solution**: Ensure the OSC listener live_loop is running in Sonic Pi:
```ruby
live_loop :mcp_listener do
  use_real_time
  code_message = sync "/osc*/mcp/code"
  begin
    eval(code_message[0])
  rescue => e
    puts "Error executing code: #{e.message}"
  end
end
```

### Port Discovery Issues

**Problem**: Server can't find Sonic Pi's port automatically.

**Solutions**:
1. Check if Sonic Pi is running: `lsof -i -P -n | grep -i sonic`
2. Manually set the port in `.env`:
   ```
   SONICPI_OSC_HOST=127.0.0.1
   SONICPI_OSC_PORT=4560
   ```
3. Use the diagnostic tool: `echo '{"tool": "diagnose", "args": {}}' | python3 -m sonicpi_mcp`

### OSC Messages Not Appearing in Cues

**Problem**: No messages appear in Sonic Pi's Cues panel.

**Solutions**:
1. Verify Sonic Pi's network settings (Prefs → Network → OSC)
2. Ensure "Allow incoming OSC messages" is enabled
3. Check that the correct IP address is configured (use `192.168.x.x` for network, `127.0.0.1` for localhost)

### Key Insights

- **Sonic Pi uses two OSC systems**: 
  - Port 4560 for cues and general OSC messages
  - A dynamic port (discovered automatically) for internal commands
- **Code execution requires a live_loop**: Sonic Pi doesn't execute arbitrary code via OSC without a listener
- **Automatic port discovery**: The server discovers Sonic Pi's ports automatically using `lsof`
- **OSC message format**: Messages sent to port 4560 appear in Cues as `/osc:sender_ip:sender_port/path`

## AI Music Generation System

The server includes a sophisticated AI-powered music generation system with two modes:

### Pattern-Based Generation (Default)
- **Works offline** - no external API required
- Uses pre-built musical patterns for common genres
- Fast and reliable for standard musical requests
- Supports: rock, techno, jazz, hip_hop, pop, blues, funk

### AI-Powered Generation (Optional)
- **Requires OpenAI API key** - set `OPENAI_API_KEY` in `.env`
- Generates custom, creative Sonic Pi code
- Handles complex and unique musical requests
- Falls back to pattern-based generation if unavailable

### Supported Musical Elements
- **Genres**: rock, jazz, techno, hip_hop, pop, blues, funk
- **Instruments**: drums, bass, piano, guitar, synth
- **Tempo**: automatic detection or specify BPM
- **Mood**: energetic, calm, intense, relaxed
- **Complexity**: simple, medium, complex patterns

## Project Structure

```
sonicpi-mcp/
├── sonicpi_mcp/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Main entry point
│   ├── server.py            # MCP server core
│   ├── schemas.py           # Data contracts and validation
│   ├── config.py            # Configuration management
│   ├── osc_client.py        # OSC communication with auto-discovery
│   ├── logging.py           # Logging system with ring buffer
│   ├── diagnostics.py       # System diagnostics and port discovery
│   ├── patterns.py          # Musical pattern library
│   └── ai_generator.py      # AI-powered music generation
├── mcp.json                 # MCP tool definitions
├── pyproject.toml           # Python dependencies and metadata
├── README.md               # This documentation
├── .env_example            # Example environment configuration
├── .env                    # Environment configuration (create from .env_example)
└── .gitignore              # Git ignore rules
```

### Key Files

- **`server.py`** - Main MCP server with all tool handlers
- **`ai_generator.py`** - Natural language to Sonic Pi code translation
- **`patterns.py`** - Pre-built musical patterns and templates
- **`osc_client.py`** - Automatic Sonic Pi port discovery and OSC communication
- **`schemas.py`** - Strict data validation for all tools
- **`mcp.json`** - Tool definitions for Cursor integration

## Future Expansion

The server is designed for future expansion:
- **Network transport support** - remote control capabilities
- **Buffer management** - manage multiple Sonic Pi buffers
- **Recording controls** - start/stop audio recording
- **Snippet library** - save and load custom patterns
- **UI/client applications** - web or desktop interfaces
- **Advanced AI features** - style transfer, chord progression analysis
- **MIDI integration** - external MIDI device support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details