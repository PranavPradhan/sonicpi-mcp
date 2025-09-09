"""AI-powered music code generation for natural language requests."""

import os
import re
from typing import Dict, List, Optional, Tuple

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .patterns import get_pattern, list_patterns, get_pattern_description


class MusicAI:
    """AI-powered music generation using patterns and OpenAI."""
    
    def __init__(self):
        """Initialize the music AI system."""
        self.openai_client = None
        self.patterns = list_patterns()
        
        # Initialize OpenAI if available and API key is set
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception:
                self.openai_client = None
    
    def parse_request(self, request: str) -> Dict[str, any]:
        """Parse a natural language music request."""
        request_lower = request.lower()
        
        # Extract musical elements
        elements = {
            "instruments": [],
            "genre": None,
            "bpm": None,
            "key": None,
            "mood": None,
            "complexity": "medium"
        }
        
        # Detect genres
        genre_patterns = {
            "rock": ["rock", "metal", "punk"],
            "jazz": ["jazz", "swing", "bebop"],
            "techno": ["techno", "electronic", "edm", "house"],
            "hip_hop": ["hip hop", "hip-hop", "rap", "trap"],
            "pop": ["pop", "commercial"],
            "blues": ["blues", "country"],
            "funk": ["funk", "funky"]
        }
        
        for genre, keywords in genre_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                elements["genre"] = genre
                break
        
        # Detect instruments
        instrument_patterns = {
            "drums": ["drum", "beat", "rhythm", "percussion"],
            "bass": ["bass", "bassline"],
            "piano": ["piano", "keys", "keyboard"],
            "guitar": ["guitar"],
            "synth": ["synth", "synthesizer", "electronic"]
        }
        
        for instrument, keywords in instrument_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                elements["instruments"].append(instrument)
        
        # Extract BPM
        bpm_match = re.search(r'(\d+)\s*bpm', request_lower)
        if bpm_match:
            elements["bpm"] = int(bpm_match.group(1))
        
        # Detect mood/energy
        if any(word in request_lower for word in ["fast", "energetic", "upbeat", "intense"]):
            elements["mood"] = "energetic"
        elif any(word in request_lower for word in ["slow", "chill", "relaxed", "calm"]):
            elements["mood"] = "calm"
        
        return elements
    
    def generate_pattern_based_code(self, elements: Dict[str, any]) -> Optional[str]:
        """Generate code using predefined patterns."""
        code_parts = []
        
        # Set BPM if specified
        bpm = elements.get("bpm", 120)
        if elements["mood"] == "energetic" and not elements.get("bpm"):
            bpm = 140
        elif elements["mood"] == "calm" and not elements.get("bpm"):
            bpm = 80
        
        # Add drum pattern if requested
        if "drums" in elements["instruments"] or "beat" in str(elements):
            genre = elements.get("genre", "rock")
            drum_code = get_pattern("drums", genre, bpm=bpm)
            if drum_code:
                code_parts.append(drum_code)
        
        # Add bass pattern
        if "bass" in elements["instruments"]:
            genre = elements.get("genre", "rock")
            bass_code = get_pattern("bass", genre)
            if bass_code:
                code_parts.append(bass_code)
        
        # Add chord progression
        if any(inst in elements["instruments"] for inst in ["piano", "guitar", "synth"]):
            genre = elements.get("genre", "pop")
            chord_code = get_pattern("chords", genre)
            if chord_code:
                code_parts.append(chord_code)
        
        return "\n\n".join(code_parts) if code_parts else None
    
    def generate_ai_code(self, request: str, elements: Dict[str, any]) -> Optional[str]:
        """Generate code using OpenAI if available."""
        if not self.openai_client:
            return None
        
        try:
            # Create a prompt for Sonic Pi code generation
            prompt = f"""
Generate Sonic Pi code for this music request: "{request}"

Musical elements detected:
- Genre: {elements.get('genre', 'not specified')}
- Instruments: {', '.join(elements['instruments']) if elements['instruments'] else 'not specified'}
- BPM: {elements.get('bpm', 'not specified')}
- Mood: {elements.get('mood', 'not specified')}

Requirements:
1. Generate valid Sonic Pi Ruby code
2. Use live_loop structures for continuous patterns
3. Include appropriate synths and samples
4. Make it musically interesting
5. Keep it concise but complete
6. Use proper timing with sleep commands

Return only the Sonic Pi code, no explanations.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Sonic Pi expert who generates creative, musical code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"AI generation failed: {e}")
            return None
    
    def generate_music_code(self, request: str) -> Tuple[str, str]:
        """
        Generate Sonic Pi code from a natural language request.
        Returns (code, method_used).
        """
        elements = self.parse_request(request)
        
        # Try AI generation first if available
        if self.openai_client:
            ai_code = self.generate_ai_code(request, elements)
            if ai_code:
                return ai_code, "ai"
        
        # Fall back to pattern-based generation
        pattern_code = self.generate_pattern_based_code(elements)
        if pattern_code:
            return pattern_code, "patterns"
        
        # Ultimate fallback - simple beat
        fallback_code = """
use_bpm 120
live_loop :simple_beat do
  sample :bd_haus
  sleep 1
  sample :sn_dub
  sleep 1
end
"""
        return fallback_code.strip(), "fallback"
    
    def suggest_improvements(self, request: str) -> List[str]:
        """Suggest ways to improve or extend the musical request."""
        suggestions = []
        
        elements = self.parse_request(request)
        
        if not elements["instruments"]:
            suggestions.append("Try specifying instruments like 'drums', 'bass', or 'piano'")
        
        if not elements["genre"]:
            suggestions.append("Consider adding a genre like 'rock', 'jazz', or 'techno'")
        
        if not elements["bpm"]:
            suggestions.append("You can specify tempo with 'at 120 BPM' or 'fast tempo'")
        
        return suggestions
