"""LLM service for intent parsing and sentence compaction."""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.models.schemas import CompactRequest

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Custom exception for LLM service errors."""
    pass


class LLMService:
    """Service for LLM operations."""

    def __init__(self):
        """Initialize the LLM service."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMServiceError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature = 0  # Deterministic responses

    async def parse_intent(self, message: str) -> Dict[str, Any]:
        """Parse natural language command into structured parameters."""
        prompt = f"""Parse this natural language command into structured parameters for an Anki assistant.

Command: {message}

Return a JSON object with these fields:
- action: "compact_examples", "rollback", "list_longest", or "list_decks"
- deck: deck name (string, required for all actions except "list_decks")
- field: field name (string, default "Example", not needed for "list_decks")
- limit: maximum number of notes (integer, default 30, not needed for "list_decks")
- preview_count: number of preview items (integer, default 5, not needed for "list_decks")
- confirm: whether to confirm (boolean, default false, not needed for "list_decks")

Examples:
- "Compact examples in deck 'News B2', preview 5, apply 30" → {{"action": "compact_examples", "deck": "News B2", "preview_count": 5, "limit": 30, "confirm": false}}
- "Rollback compacted examples in 'News B2'" → {{"action": "rollback", "deck": "News B2"}}
- "List 10 longest examples in 'News B2'" → {{"action": "list_longest", "deck": "News B2", "limit": 10}}
- "List top 10 cards in the A deck" → {{"action": "list_longest", "deck": "A", "limit": 10}}
- "List 5 longest Front field in A deck" → {{"action": "list_longest", "deck": "A", "field": "Front", "limit": 5}}
- "Show longest Back fields in deck B" → {{"action": "list_longest", "deck": "B", "field": "Back"}}
- "List my decks" → {{"action": "list_decks"}}
- "Show all decks" → {{"action": "list_decks"}}

JSON response:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            content = content.strip()
            if not content.startswith("{"):
                raise LLMServiceError("Invalid JSON response format")
            
            result = json.loads(content)
            
            # Validate required fields
            if "action" not in result:
                raise LLMServiceError("Missing required field: action")
            
            # For actions other than list_decks, deck is required
            if result["action"] != "list_decks" and "deck" not in result:
                raise LLMServiceError("Missing required field: deck")
            
            # Set defaults
            if result["action"] != "list_decks":
                result.setdefault("field", "Example")
                result.setdefault("limit", 30)
                result.setdefault("preview_count", 5)
                result.setdefault("confirm", False)
            
            return result
            
        except json.JSONDecodeError as e:
            raise LLMServiceError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise LLMServiceError(f"LLM API error: {e}")

    async def compact_sentence(self, target_word: str, sentence: str) -> str:
        """Compact a sentence while preserving the target word."""
        prompt = f"""Compact this example sentence while following these constraints:

Target word: {target_word}
Current sentence: {sentence}

Constraints:
1. Keep the target word EXACTLY as given (unchanged form)
2. Make it 10-16 words total
3. Use CEFR B2 level vocabulary and everyday context
4. No named entities, no rare idioms
5. Use the most common sense of the word
6. Ensure the target word is present in the output

Return only the compacted sentence, nothing else."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=200
            )
            
            compacted = response.choices[0].message.content.strip()
            
            # Validate that target word is present
            if target_word.lower() not in compacted.lower():
                logger.warning(f"Target word '{target_word}' not found in compacted sentence")
                # Try one more time with more explicit instructions
                retry_prompt = f"""The target word '{target_word}' must appear in the compacted sentence.

Target word: {target_word}
Current sentence: {sentence}

Compact to 10-16 words, keeping '{target_word}' exactly as is:"""
                
                retry_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": retry_prompt}],
                    temperature=self.temperature,
                    max_tokens=200
                )
                
                compacted = retry_response.choices[0].message.content.strip()
                
                # Final validation
                if target_word.lower() not in compacted.lower():
                    raise LLMServiceError(f"Target word '{target_word}' not found in compacted sentence after retry")
            
            return compacted
            
        except Exception as e:
            raise LLMServiceError(f"Failed to compact sentence: {e}")

    async def health_check(self) -> bool:
        """Check if LLM service is available."""
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False

    async def compact_multiple_sentences(
        self, 
        sentences_data: list, 
        rate_limit_ms: int = 250
    ) -> list:
        """Compact multiple sentences with rate limiting."""
        results = []
        
        for i, data in enumerate(sentences_data):
            try:
                compacted = await self.compact_sentence(
                    target_word=data["target"],
                    sentence=data["sentence"]
                )
                results.append({
                    "note_id": data["note_id"],
                    "target": data["target"],
                    "original": data["sentence"],
                    "compacted": compacted,
                    "success": True
                })
                
                # Rate limiting
                if i < len(sentences_data) - 1:  # Don't sleep after last item
                    await asyncio.sleep(rate_limit_ms / 1000)
                    
            except Exception as e:
                logger.error(f"Failed to compact sentence for note {data['note_id']}: {e}")
                results.append({
                    "note_id": data["note_id"],
                    "target": data["target"],
                    "original": data["sentence"],
                    "compacted": None,
                    "success": False,
                    "error": str(e)
                })
        
        return results
