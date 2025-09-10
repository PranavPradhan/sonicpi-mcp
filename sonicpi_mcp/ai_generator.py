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
Generate professional Sonic Pi code for this music request: "{request}"

Musical elements detected:
- Genre: {elements.get('genre', 'not specified')}
- Instruments: {', '.join(elements['instruments']) if elements['instruments'] else 'not specified'}
- BPM: {elements.get('bpm', 'not specified')}
- Mood: {elements.get('mood', 'not specified')}

Elite Professional Requirements:
1. Generate world-class, multi-layered Sonic Pi Ruby code with studio-quality production
2. Use 5+ live_loop structures for complex, sophisticated arrangements
3. Include advanced synths (:blade, :dsaw, :fm, :prophet, :tb303, :saw, :piano, etc.)
4. Add professional effects chains (reverb, echo, distortion, filters, compression)
5. Create sophisticated musical progressions with advanced harmony
6. Use proper jazz/classical chord voicings and walking bass lines
7. Include dynamic amplitude, effect control, and musical expression
8. Make it sound like a professional studio production
9. Use precise timing with sleep commands and musical phrasing
10. Add complex musical structure, form, and development

Elite Techniques to Master:
- Multiple live_loop layers (drums, bass, melody, pads, effects, percussion)
- Complex with_fx chains for professional studio sound
- Advanced chord progressions (ii-V-I, jazz standards, modal harmony)
- Sophisticated sample manipulation with rate, amp, and filter parameters
- Dynamic control, musical expression, and human-like performance
- Advanced rhythmic patterns (swing, polyrhythms, complex time signatures)
- Professional arrangement techniques (intro, verse, chorus, bridge, outro)
- Musical development and variation throughout the composition

Return only the Sonic Pi code, no explanations.
"""
            
            # Try the most advanced models first, with fallbacks
            models_to_try = ["gpt-5", "gpt-4o", "gpt-4-turbo", "gpt-4"]
            response = None
            
            for model in models_to_try:
                try:
                    # Use max_completion_tokens for GPT-5, max_tokens for others
                    if model == "gpt-5":
                        response = self.openai_client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": "You are an elite Sonic Pi music producer and composer with deep expertise in music theory, jazz harmony, electronic music production, and advanced programming. You create sophisticated, multi-layered musical compositions that rival professional studio productions. Your code demonstrates mastery of: complex chord progressions, advanced synthesis techniques, professional effects chains, dynamic musical arrangements, and sophisticated rhythmic patterns. Generate code that sounds like it was created by a world-class music producer."},
                                {"role": "user", "content": prompt}
                            ],
                            max_completion_tokens=4000,  # GPT-5 uses max_completion_tokens
                            temperature=1.0   # GPT-5 only supports default temperature
                        )
                    else:
                        response = self.openai_client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": "You are an elite Sonic Pi music producer and composer with deep expertise in music theory, jazz harmony, electronic music production, and advanced programming. You create sophisticated, multi-layered musical compositions that rival professional studio productions. Your code demonstrates mastery of: complex chord progressions, advanced synthesis techniques, professional effects chains, dynamic musical arrangements, and sophisticated rhythmic patterns. Generate code that sounds like it was created by a world-class music producer."},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=4000,  # Other models use max_tokens
                            temperature=0.9   # High creativity for musical variety and sophistication
                        )
                    print(f"Successfully used {model} for AI generation")
                    break
                except Exception as e:
                    print(f"Failed to use {model}: {e}")
                    continue
            
            if not response:
                print("All AI models failed, falling back to patterns")
                return None
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```ruby"):
                content = content[7:]  # Remove ```ruby
            elif content.startswith("```"):
                content = content[3:]   # Remove ```
            
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            
            return content.strip()
        
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
