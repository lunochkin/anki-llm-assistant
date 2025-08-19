"""Tests for the logic service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.logic import LogicService, LogicServiceError
from app.models.schemas import (
    CompactRequest, CompactPreviewResponse, PreviewDiff,
    ApplySummary, ListLongestResponse, ListLongestItem,
    RollbackResponse, ListCardsResponse, ListCardsItem
)


@pytest.fixture
def mock_anki_client():
    """Mock AnkiConnect client."""
    client = AsyncMock()
    client.find_notes_for_compaction.return_value = [1, 2, 3]
    client.notes_info.return_value = [
        {
            "noteId": 1,
            "fields": {
                "Word": {"value": "example"},
                "Example": {"value": "This is a very long example sentence that needs to be compacted."}
            }
        },
        {
            "noteId": 2,
            "fields": {
                "Word": {"value": "test"},
                "Example": {"value": "Another long example sentence for testing purposes."}
            }
        },
        {
            "noteId": 3,
            "fields": {
                "Word": {"value": "sample"},
                "Example": {"value": "A third example sentence that is also quite long."}
            }
        }
    ]
    client.extract_headword.return_value = "example"
    client.build_query.return_value = 'deck:"Test Deck" has:field:Example'
    client.find_notes_for_rollback.return_value = [1, 2]
    return client


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    service = AsyncMock()
    service.compact_multiple_sentences.return_value = [
        {
            "note_id": 1,
            "target": "example",
            "original": "This is a very long example sentence that needs to be compacted.",
            "compacted": "This is a compact example sentence.",
            "success": True
        },
        {
            "note_id": 2,
            "target": "test",
            "original": "Another long example sentence for testing purposes.",
            "compacted": "This is a compact test sentence.",
            "success": True
        },
        {
            "note_id": 3,
            "target": "sample",
            "original": "A third example sentence that is also quite long.",
            "compacted": "This is a compact sample sentence.",
            "success": True
        }
    ]
    return service


@pytest.fixture
def logic_service(mock_anki_client, mock_llm_service):
    """Logic service with mocked dependencies."""
    with patch('app.services.logic.AnkiConnectClient', return_value=mock_anki_client):
        with patch('app.services.logic.LLMService', return_value=mock_llm_service):
            service = LogicService()
            service.anki_client = mock_anki_client
            service.llm_service = mock_llm_service
            return service


class TestCompactExamples:
    """Test compact examples functionality."""
    
    async def test_compact_examples_preview_mode(self, logic_service, mock_anki_client, mock_llm_service):
        """Test compact examples in preview mode."""
        request = CompactRequest(
            deck="Test Deck",
            field="Example",
            preview_count=2,
            limit=3
        )
        
        result = await logic_service.compact_examples(
            deck=request.deck,
            field=request.field,
            preview_count=request.preview_count,
            limit=request.limit,
            dry_run=True
        )
        
        assert isinstance(result, CompactPreviewResponse)
        assert result.count == 3
        assert len(result.diffs) == 2  # preview_count
        assert result.needs_confirmation is False
        assert result.confirm_token is None
        
        # Verify Anki client calls
        mock_anki_client.find_notes_for_compaction.assert_called_once()
        mock_anki_client.notes_info.assert_called_once_with([1, 2, 3])
        
        # Verify LLM service calls
        mock_llm_service.compact_multiple_sentences.assert_called_once()
    
    async def test_compact_examples_apply_mode(self, logic_service, mock_anki_client, mock_llm_service):
        """Test compact examples in apply mode."""
        result = await logic_service.compact_examples(
            deck="Test Deck",
            field="Example",
            preview_count=2,
            limit=3,
            dry_run=False
        )
        
        assert isinstance(result, CompactPreviewResponse)
        assert result.count == 3
        assert result.needs_confirmation is True
        assert result.confirm_token is not None
        
        # Verify confirmation token is stored
        assert result.confirm_token in logic_service.confirm_tokens
    
    async def test_compact_examples_no_notes_found(self, logic_service, mock_anki_client):
        """Test compact examples when no notes are found."""
        mock_anki_client.find_notes_for_compaction.return_value = []
        
        result = await logic_service.compact_examples(
            deck="Test Deck",
            field="Example"
        )
        
        assert result.count == 0
        assert result.diffs == []
        assert result.needs_confirmation is False
    
    async def test_compact_examples_anki_error(self, logic_service, mock_anki_client):
        """Test compact examples when Anki client fails."""
        mock_anki_client.find_notes_for_compaction.side_effect = Exception("Anki error")
        
        with pytest.raises(LogicServiceError, match="Compaction failed"):
            await logic_service.compact_examples(
                deck="Test Deck",
                field="Example"
            )


class TestApplyCompaction:
    """Test apply compaction functionality."""
    
    async def test_apply_compaction_success(self, logic_service, mock_anki_client):
        """Test successful application of compaction."""
        # Setup confirmation token
        token = "test_token_123"
        logic_service.confirm_tokens[token] = {
            "deck": "Test Deck",
            "field": "Example",
            "note_ids": [1, 2],
            "diffs": [
                PreviewDiff(
                    note_id=1,
                    word="example",
                    old="Old sentence",
                    new="New sentence"
                ),
                PreviewDiff(
                    note_id=2,
                    word="test",
                    old="Old test sentence",
                    new="New test sentence"
                )
            ]
        }
        
        # Mock successful operations
        mock_anki_client.backup_field.return_value = True
        mock_anki_client.update_note_fields.return_value = None
        mock_anki_client.add_tags.return_value = None
        
        result = await logic_service.apply_compaction(token)
        
        assert isinstance(result, ApplySummary)
        assert result.updated == 2
        assert result.skipped == 0
        assert result.tagged == 2
        
        # Verify token was cleaned up
        assert token not in logic_service.confirm_tokens
        
        # Verify Anki operations were called
        assert mock_anki_client.backup_field.call_count == 2
        assert mock_anki_client.update_note_fields.call_count == 2
        assert mock_anki_client.add_tags.call_count == 2
    
    async def test_apply_compaction_invalid_token(self, logic_service):
        """Test apply compaction with invalid token."""
        with pytest.raises(LogicServiceError, match="Invalid confirmation token"):
            await logic_service.apply_compaction("invalid_token")
    
    async def test_apply_compaction_partial_failure(self, logic_service, mock_anki_client):
        """Test apply compaction with some failures."""
        token = "test_token_123"
        logic_service.confirm_tokens[token] = {
            "deck": "Test Deck",
            "field": "Example",
            "note_ids": [1, 2],
            "diffs": [
                PreviewDiff(
                    note_id=1,
                    word="example",
                    old="Old sentence",
                    new="New sentence"
                ),
                PreviewDiff(
                    note_id=2,
                    word="test",
                    old="Old test sentence",
                    new="New test sentence"
                )
            ]
        }
        
        # Mock first operation success, second failure
        mock_anki_client.backup_field.side_effect = [True, False]
        mock_anki_client.update_note_fields.return_value = None
        mock_anki_client.add_tags.return_value = None
        
        result = await logic_service.apply_compaction(token)
        
        assert result.updated == 1
        assert result.skipped == 1
        assert result.tagged == 1


class TestRollbackCompacted:
    """Test rollback functionality."""
    
    async def test_rollback_success(self, logic_service, mock_anki_client):
        """Test successful rollback."""
        mock_anki_client.find_notes_for_rollback.return_value = [1, 2]
        mock_anki_client.notes_info.return_value = [
            {
                "noteId": 1,
                "fields": {
                    "Example": {"value": "Compacted sentence"},
                    "Example_Original": {"value": "Original long sentence"}
                }
            },
            {
                "noteId": 2,
                "fields": {
                    "Example": {"value": "Another compacted sentence"},
                    "Example_Original": {"value": "Another original sentence"}
                }
            }
        ]
        
        result = await logic_service.rollback_compacted("Test Deck", "Example")
        
        assert isinstance(result, RollbackResponse)
        assert result.restored == 2
        assert result.untagged == 2
        
        # Verify Anki operations were called
        assert mock_anki_client.update_note_fields.call_count == 2
        assert mock_anki_client.remove_tags.call_count == 2
    
    async def test_rollback_no_notes(self, logic_service, mock_anki_client):
        """Test rollback when no notes are found."""
        mock_anki_client.find_notes_for_rollback.return_value = []
        
        result = await logic_service.rollback_compacted("Test Deck", "Example")
        
        assert result.restored == 0
        assert result.untagged == 0


class TestListLongestExamples:
    """Test list longest examples functionality."""
    
    async def test_list_longest_success(self, logic_service, mock_anki_client):
        """Test successful listing of longest examples."""
        mock_anki_client.find_notes.return_value = [1, 2, 3]
        mock_anki_client.notes_info.return_value = [
            {
                "noteId": 1,
                "fields": {
                    "Example": {"value": "This is a very long example sentence with many words"}
                }
            },
            {
                "noteId": 2,
                "fields": {
                    "Example": {"value": "Short sentence"}
                }
            },
            {
                "noteId": 3,
                "fields": {
                    "Example": {"value": "This is another long example sentence that has many words in it"}
                }
            }
        ]
        
        result = await logic_service.list_longest_examples("Test Deck", "Example", 2)
        
        assert isinstance(result, ListLongestResponse)
        assert result.total_found == 3
        assert len(result.items) == 2
        
        # Verify items are sorted by length (descending)
        assert result.items[0].length > result.items[1].length
        assert result.items[0].note_id == 3  # Longest sentence
        assert result.items[1].note_id == 1  # Second longest
    
    async def test_list_longest_no_notes(self, logic_service, mock_anki_client):
        """Test listing when no notes are found."""
        mock_anki_client.find_notes.return_value = []
        
        result = await logic_service.list_longest_examples("Test Deck", "Example")
        
        assert result.total_found == 0
        assert result.items == []


class TestListCards:
    """Test list cards functionality."""
    
    async def test_list_cards_with_filter(self, logic_service, mock_anki_client, mock_llm_service):
        """Test list cards with LLM filtering."""
        # Mock the LLM filtering response
        mock_llm_service.filter_cards_by_description.return_value = [
            {
                "note_id": 1,
                "score": 0.95,
                "reasoning": "Perfect match for business vocabulary"
            },
            {
                "note_id": 2,
                "score": 0.87,
                "reasoning": "Good match with business context"
            }
        ]
        
        result = await logic_service.list_cards(
            deck="Business English",
            field="Example",
            filter_description="business vocabulary",
            limit=5
        )
        
        assert isinstance(result, ListCardsResponse)
        assert result.total_found == 3  # From mock_anki_client
        assert len(result.items) == 2
        assert result.filter_applied == "business vocabulary"
        
        # Check first item
        first_item = result.items[0]
        assert first_item.note_id == 1
        assert first_item.score == 0.95
        assert first_item.reasoning == "Perfect match for business vocabulary"
        
        # Verify LLM service was called
        mock_llm_service.filter_cards_by_description.assert_called_once()
        call_args = mock_llm_service.filter_cards_by_description.call_args
        assert call_args[0][0] == "business vocabulary"  # filter_description
        assert len(call_args[0][1]) == 3  # cards_data
        assert call_args[0][2] == 5  # limit
    
    async def test_list_cards_without_filter(self, logic_service, mock_anki_client, mock_llm_service):
        """Test list cards without filter (natural deck order)."""
        result = await logic_service.list_cards(
            deck="Test Deck",
            field="Example",
            filter_description="",
            limit=3,
            position="top"
        )
        
        assert isinstance(result, ListCardsResponse)
        assert result.total_found == 3
        assert len(result.items) == 3
        assert result.filter_applied == "No filter applied - natural deck order (top)"
        
        # Should be in natural deck order (as returned by Anki) - top cards
        assert result.items[0].note_id == 1  # First note in natural order
        assert result.items[1].note_id == 2  # Second note in natural order
        assert result.items[2].note_id == 3  # Third note in natural order
        
        # All cards should have same score when no filtering
        assert all(item.score == 1.0 for item in result.items)
        assert all("Natural deck order - top" in item.reasoning for item in result.items)
        
        # LLM service should not be called when no filter
        mock_llm_service.filter_cards_by_description.assert_not_called()
    
    async def test_list_cards_bottom_position(self, logic_service, mock_anki_client, mock_llm_service):
        """Test list cards with bottom position (natural deck order)."""
        result = await logic_service.list_cards(
            deck="Test Deck",
            field="Example",
            filter_description="",
            limit=2,
            position="bottom"
        )
        
        assert isinstance(result, ListCardsResponse)
        assert result.total_found == 3
        assert len(result.items) == 2
        assert result.filter_applied == "No filter applied - natural deck order (bottom)"
        
        # Should be in natural deck order (as returned by Anki) - bottom cards
        assert result.items[0].note_id == 2  # Second to last note in natural order
        assert result.items[1].note_id == 3  # Last note in natural order
        
        # All cards should have same score when no filtering
        assert all(item.score == 1.0 for item in result.items)
        assert all("Natural deck order - bottom" in item.reasoning for item in result.items)
        
        # LLM service should not be called when no filter
        mock_llm_service.filter_cards_by_description.assert_not_called()
    
    async def test_list_cards_no_notes_found(self, logic_service, mock_anki_client):
        """Test list cards when no notes are found."""
        mock_anki_client.find_notes.return_value = []
        
        result = await logic_service.list_cards(
            deck="Empty Deck",
            field="Example",
            filter_description="any filter",
            limit=5
        )
        
        assert isinstance(result, ListCardsResponse)
        assert result.total_found == 0
        assert result.items == []
        assert result.filter_applied == "any filter"
    
    async def test_list_cards_field_auto_detection(self, logic_service, mock_anki_client):
        """Test list cards with field auto-detection."""
        # Mock no notes found with "Example" field
        mock_anki_client.find_notes.return_value = []
        # Mock auto-detection finding "Back" field
        mock_anki_client.detect_content_field.return_value = "Back"
        # Mock finding notes with "Back" field
        mock_anki_client.find_notes.side_effect = [[], [1, 2, 3]]
        
        result = await logic_service.list_cards(
            deck="Test Deck",
            field="Example",
            filter_description="",
            limit=3
        )
        
        assert result.total_found == 3
        # Should have called detect_content_field
        mock_anki_client.detect_content_field.assert_called_once_with("Test Deck")

    async def test_list_cards_deck_name_resolution(self, logic_service, mock_anki_client, mock_llm_service):
        """Test list cards with deck name resolution."""
        # Mock no notes found initially
        mock_anki_client.find_notes.return_value = []
        # Mock available decks
        mock_anki_client.get_deck_names.return_value = ["Cambridge English B2", "Cambridge Advanced", "Business English"]
        # Mock successful resolution
        mock_anki_client.find_best_matching_deck.return_value = "Cambridge English B2"
        # Mock finding notes after resolution
        mock_anki_client.find_notes.side_effect = [[], [1, 2, 3]]
        
        result = await logic_service.list_cards(
            deck="Cambridge",
            field="Example",
            filter_description="",
            limit=3,
            position="top"
        )
        
        assert isinstance(result, ListCardsResponse)
        assert result.total_found == 3
        assert result.deck_resolved == "Cambridge"  # Original deck name
        assert len(result.items) == 3
        
        # Verify deck resolution was attempted
        mock_anki_client.find_best_matching_deck.assert_called_once_with("Cambridge")
        mock_anki_client.get_deck_names.assert_called_once()


class TestErrorHandling:
    """Test error handling."""
    
    async def test_anki_client_error_propagation(self, logic_service, mock_anki_client):
        """Test that Anki client errors are properly propagated."""
        mock_anki_client.find_notes_for_compaction.side_effect = Exception("Anki connection failed")
        
        with pytest.raises(LogicServiceError, match="Compaction failed"):
            await logic_service.compact_examples("Test Deck", "Example")
    
    async def test_llm_service_error_propagation(self, logic_service, mock_anki_client, mock_llm_service):
        """Test that LLM service errors are properly propagated."""
        mock_anki_client.find_notes_for_compaction.return_value = [1]
        mock_anki_client.notes_info.return_value = [
            {
                "noteId": 1,
                "fields": {
                    "Word": {"value": "example"},
                    "Example": {"value": "Test sentence"}
                }
            }
        ]
        mock_llm_service.compact_multiple_sentences.side_effect = Exception("LLM API failed")
        
        with pytest.raises(LogicServiceError, match="Compaction failed"):
            await logic_service.compact_examples("Test Deck", "Example")


if __name__ == "__main__":
    pytest.main([__file__])
