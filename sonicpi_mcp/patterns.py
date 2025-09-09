"""Music pattern library for common Sonic Pi structures."""

from typing import Dict, List, Optional

# Common drum patterns
DRUM_PATTERNS = {
    "rock": {
        "description": "Classic rock drum beat",
        "bpm": 120,
        "code": """
use_bpm {bpm}
live_loop :rock_drums do
  sample :bd_haus  # Kick on 1 and 3
  sleep 1
  sample :sn_dub   # Snare on 2 and 4
  sleep 1
  sample :bd_haus
  sleep 1
  sample :sn_dub
  sleep 1
end
""".strip()
    },
    
    "techno": {
        "description": "Four-on-the-floor techno beat",
        "bpm": 128,
        "code": """
use_bpm {bpm}
live_loop :techno_kick do
  sample :bd_tek, amp: 1.5
  sleep 1
end

live_loop :techno_hats do
  sample :drum_cymbal_closed, amp: 0.5
  sleep 0.5
end
""".strip()
    },
    
    "jazz": {
        "description": "Swing jazz drum pattern",
        "bpm": 140,
        "code": """
use_bpm {bpm}
live_loop :jazz_drums do
  sample :bd_soft
  sleep 1
  sample :drum_snare_soft, amp: 0.7
  sleep 1.5
  sample :bd_soft
  sleep 0.5
  sample :drum_snare_soft, amp: 0.7
  sleep 1
end
""".strip()
    },
    
    "hip_hop": {
        "description": "Hip-hop drum pattern with emphasis",
        "bpm": 90,
        "code": """
use_bpm {bpm}
live_loop :hiphop_drums do
  sample :bd_boom  # Heavy kick
  sleep 1
  sample :sn_dub, amp: 1.2  # Snappy snare
  sleep 1
  sample :bd_boom
  sleep 0.5
  sample :bd_boom
  sleep 0.5
  sample :sn_dub, amp: 1.2
  sleep 1
end
""".strip()
    }
}

# Bass patterns
BASS_PATTERNS = {
    "rock": {
        "description": "Rock bass line",
        "code": """
live_loop :rock_bass do
  use_synth :fm
  play :e2, release: 0.8, amp: 1.5
  sleep 1
  play :e2, release: 0.4, amp: 1
  sleep 0.5
  play :g2, release: 0.4, amp: 1
  sleep 0.5
  play :e2, release: 0.8, amp: 1.5
  sleep 1
  play :d2, release: 0.8, amp: 1.2
  sleep 1
end
""".strip()
    },
    
    "funk": {
        "description": "Funky bass line with rhythm",
        "code": """
live_loop :funk_bass do
  use_synth :tb303
  play :c2, release: 0.2, cutoff: 70, amp: 1.5
  sleep 0.25
  sleep 0.25
  play :c2, release: 0.1, cutoff: 60, amp: 1
  sleep 0.25
  play :eb2, release: 0.3, cutoff: 80, amp: 1.2
  sleep 0.25
  play :c2, release: 0.2, cutoff: 70, amp: 1.5
  sleep 1
end
""".strip()
    }
}

# Chord progressions
CHORD_PROGRESSIONS = {
    "pop": {
        "description": "Popular I-V-vi-IV progression",
        "code": """
live_loop :pop_chords do
  use_synth :blade
  play_chord [:c4, :e4, :g4], release: 1.5, amp: 0.8  # C major
  sleep 2
  play_chord [:g3, :b3, :d4], release: 1.5, amp: 0.8  # G major
  sleep 2
  play_chord [:a3, :c4, :e4], release: 1.5, amp: 0.8  # A minor
  sleep 2
  play_chord [:f3, :a3, :c4], release: 1.5, amp: 0.8  # F major
  sleep 2
end
""".strip()
    },
    
    "blues": {
        "description": "12-bar blues progression",
        "code": """
live_loop :blues_chords do
  use_synth :piano
  # I chord (4 bars)
  4.times do
    play_chord [:c3, :e3, :g3], release: 0.8, amp: 0.7
    sleep 1
  end
  
  # IV chord (2 bars)
  2.times do
    play_chord [:f3, :a3, :c4], release: 0.8, amp: 0.7
    sleep 1
  end
  
  # I chord (2 bars)
  2.times do
    play_chord [:c3, :e3, :g3], release: 0.8, amp: 0.7
    sleep 1
  end
  
  # V-IV-I-I
  play_chord [:g3, :b3, :d4], release: 0.8, amp: 0.7
  sleep 1
  play_chord [:f3, :a3, :c4], release: 0.8, amp: 0.7
  sleep 1
  play_chord [:c3, :e3, :g3], release: 0.8, amp: 0.7
  sleep 2
end
""".strip()
    }
}

def get_pattern(category: str, pattern_name: str, **kwargs) -> Optional[str]:
    """Get a pattern by category and name, with optional parameter substitution."""
    patterns = {
        "drums": DRUM_PATTERNS,
        "bass": BASS_PATTERNS,
        "chords": CHORD_PROGRESSIONS
    }
    
    if category not in patterns:
        return None
    
    pattern_dict = patterns[category].get(pattern_name)
    if not pattern_dict:
        return None
    
    code = pattern_dict["code"]
    
    # Apply parameter substitution
    if "bpm" in pattern_dict:
        kwargs.setdefault("bpm", pattern_dict["bpm"])
    
    # Ensure we have a valid BPM
    if "bpm" in kwargs and kwargs["bpm"] is None:
        kwargs["bpm"] = pattern_dict.get("bpm", 120)
    
    try:
        return code.format(**kwargs)
    except KeyError:
        return code

def list_patterns() -> Dict[str, List[str]]:
    """List all available patterns by category."""
    return {
        "drums": list(DRUM_PATTERNS.keys()),
        "bass": list(BASS_PATTERNS.keys()),
        "chords": list(CHORD_PROGRESSIONS.keys())
    }

def get_pattern_description(category: str, pattern_name: str) -> Optional[str]:
    """Get description of a specific pattern."""
    patterns = {
        "drums": DRUM_PATTERNS,
        "bass": BASS_PATTERNS,
        "chords": CHORD_PROGRESSIONS
    }
    
    if category not in patterns:
        return None
    
    pattern_dict = patterns[category].get(pattern_name)
    return pattern_dict["description"] if pattern_dict else None
