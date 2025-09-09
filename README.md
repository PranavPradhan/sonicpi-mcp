# Sonic Pi MCP Server

A local MCP server that controls Sonic Pi via OSC with AI-powered music generation.

## How It Works

1. **MCP Server** receives natural language requests
2. **AI Generator** converts requests to Sonic Pi code (patterns or OpenAI)
3. **OSC Client** sends code to Sonic Pi via OSC
4. **Sonic Pi** executes the code and plays music

## Setup

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### 2. Configure Sonic Pi
Add this code to Sonic Pi and click "Run":
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

### 3. Optional: Add OpenAI API Key
```bash
cp .env_example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here
```

### 4. Run Server
```bash
python -m sonicpi_mcp
```

## Usage

### Via Cursor (Recommended)
1. Ensure server is running
2. Use commands like: "create a rock beat", "make techno music", "play jazz piano"

### Via Command Line
```bash
# Create and play music
echo '{"tool": "create_and_play", "args": {"request": "create a rock drum beat"}}' | python3 -m sonicpi_mcp

# Run Sonic Pi code directly
echo '{"tool": "run_code", "args": {"source": "play 60, amp: 2"}}' | python3 -m sonicpi_mcp

# Set BPM
echo '{"tool": "set_bpm", "args": {"bpm": 120}}' | python3 -m sonicpi_mcp

# Stop all
echo '{"tool": "stop_all", "args": {}}' | python3 -m sonicpi_mcp
```

## Available Tools

- **`create_and_play`** - Generate and play music from natural language
- **`run_code`** - Execute Sonic Pi code directly
- **`set_bpm`** - Set tempo
- **`stop_all`** - Stop all audio
- **`cue`** - Send cue messages
- **`generate_music`** - Generate code without playing
- **`list_patterns`** - Show available patterns
- **`get_pattern`** - Get specific pattern
- **`tail_logs`** - View recent logs
- **`diagnose`** - Check connection status

## Troubleshooting

**No sound?** Ensure the Sonic Pi listener live_loop is running.

**Port issues?** Server auto-discovers Sonic Pi's port. Check with: `echo '{"tool": "diagnose", "args": {}}' | python3 -m sonicpi_mcp`

**OSC not working?** Check Sonic Pi's Network settings and enable "Allow incoming OSC messages".