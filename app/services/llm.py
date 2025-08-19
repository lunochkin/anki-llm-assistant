"""LLM service for intent parsing and sentence compaction."""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
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
- action: "compact_examples", "rollback", "list_longest", "list_cards", or "list_decks"
- deck: deck name (string, required for all actions except "list_decks")
- field: field name (string, default "Example", not needed for "list_decks")
- limit: maximum number of notes (integer, default 30, not needed for "list_decks")
- preview_count: number of preview items (integer, default 5, not needed for "list_decks")
- confirm: whether to confirm (boolean, default false, not needed for "list_decks")
- filter_description: natural language description for filtering (string, only for "list_cards")
- position: "top" or "bottom" for list_cards (string, default "top", only for "list_cards")

Examples:
- "Compact examples in deck 'News B2', preview 5, apply 30" → {{"action": "compact_examples", "deck": "News B2", "preview_count": 5, "limit": 30, "confirm": false}}
- "Rollback compacted examples in 'News B2'" → {{"action": "rollback", "deck": "News B2"}}
- "List 10 longest examples in 'News B2'" → {{"action": "list_longest", "deck": "News B2", "limit": 10}}
- "List top 10 cards in the A deck" → {{"action": "list_longest", "deck": "A", "limit": 10}}
- "List 5 longest Front field in A deck" → {{"action": "list_longest", "deck": "A", "field": "Front", "limit": 5}}
- "Show longest Back fields in deck B" → {{"action": "list_longest", "deck": "B", "field": "Back"}}
- "Find cards with business vocabulary in deck 'Business English'" → {{"action": "list_cards", "deck": "Business English", "filter_description": "business vocabulary", "limit": 10}}
- "Show me cards about travel in deck 'Travel Phrases'" → {{"action": "list_cards", "deck": "Travel Phrases", "filter_description": "travel related content", "limit": 5}}
- "List bottom 5 cards in deck A" → {{"action": "list_cards", "deck": "A", "position": "bottom", "limit": 5}}
- "Show top 10 cards in deck B" → {{"action": "list_cards", "deck": "B", "position": "top", "limit": 10}}
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
                
                # Set default for filter_description if it's a list_cards action
                if result["action"] == "list_cards":
                    result.setdefault("filter_description", "")
                    result.setdefault("position", "top")
            
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

    async def resolve_deck_name(self, partial_name: str, available_decks: List[str]) -> Optional[str]:
        """Use LLM to intelligently resolve partial deck names to exact names."""
        if not partial_name or not available_decks:
            return None
        
        prompt = f"""You are helping to resolve a partial deck name to an exact deck name from a list of available decks.

Partial deck name: "{partial_name}"

Available decks:
{chr(10).join(f"- {deck}" for deck in available_decks)}

Based on the partial name "{partial_name}", which deck from the list above is most likely what the user wants?

Return only the exact deck name from the list, nothing else. If no good match exists, return "NO_MATCH".

Examples:
- Partial: "Cambridge" → might match "Cambridge English B2" or "Cambridge Advanced"
- Partial: "Business" → might match "Business English" or "Business Vocabulary"
- Partial: "Travel" → might match "Travel Phrases" or "Travel Vocabulary"

Exact deck name:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=100
            )
            
            resolved_name = response.choices[0].message.content.strip()
            
            # Validate that the resolved name is in the available decks
            if resolved_name in available_decks:
                return resolved_name
            elif resolved_name == "NO_MATCH":
                return None
            else:
                # Try to find a close match if LLM returned something not in the list
                for deck in available_decks:
                    if resolved_name.lower() in deck.lower() or deck.lower() in resolved_name.lower():
                        return deck
                return None
                
        except Exception as e:
            logger.warning(f"Failed to resolve deck name '{partial_name}' with LLM: {e}")
            return None

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

    async def filter_cards_by_description(
        self, 
        filter_description: str, 
        cards_data: list,
        limit: int = 10
    ) -> list:
        """Filter cards based on natural language description using LLM."""
        prompt = f"""You are an expert at analyzing language learning cards. 
Given a description of what to look for, analyze each card and score it from 0.0 to 1.0 based on relevance.

Filter description: {filter_description}

For each card, return a JSON object with:
- note_id: the note ID
- score: relevance score from 0.0 (completely irrelevant) to 1.0 (perfectly matches)
- reasoning: brief explanation of why this score was given

Analyze these cards and return a JSON array of results, sorted by score (highest first):

{json.dumps(cards_data, indent=2)}

Return only the JSON array, nothing else."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            content = content.strip()
            if not content.startswith("["):
                raise LLMServiceError("Invalid JSON response format - expected array")
            
            results = json.loads(content)
            
            # Validate and sort results
            if not isinstance(results, list):
                raise LLMServiceError("Expected array response")
            
            # Sort by score (descending) and limit results
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            results = results[:limit]
            
            return results
            
        except json.JSONDecodeError as e:
            raise LLMServiceError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise LLMServiceError(f"LLM API error: {e}")
