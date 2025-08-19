"""Tests for the logic service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.logic import LogicService, LogicServiceError
from app.models.schemas import (
    CompactRequest, CompactPreviewResponse, PreviewDiff,
    ApplySummary, ListLongestResponse, ListLongestItem,
    RollbackResponse
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
