# Services Architecture

This directory contains the refactored service layer that follows the Single Responsibility Principle (SRP). The monolithic `LogicService` has been broken down into focused, specialized services.

## Service Overview

### 📋 LogicService (`logic.py`)
**Role**: Orchestration facade that coordinates specialized services  
**Responsibilities**:
- Acts as a single entry point for business operations
- Delegates to specialized services
- Provides uniform error handling and logging
- Maintains backward compatibility with existing APIs

**Methods**:
- `compact_examples()` - Delegates to CompactionService
- `apply_compaction()` - Delegates to CompactionService  
- `rollback_compacted()` - Delegates to CompactionService
- `list_cards()` - Delegates to CardService
- `list_decks()` - Delegates to DeckService

### 🔄 CompactionService (`compaction.py`)
**Role**: Handles all example compaction operations  
**Responsibilities**:
- Example sentence compaction using LLM
- Confirmation token management
- Backup and restore operations
- Tagging compacted notes

**Methods**:
- `compact_examples()` - Preview/apply sentence compaction
- `apply_compaction()` - Apply changes using confirmation token
- `rollback_compacted()` - Restore original examples

**Dependencies**: AnkiConnectClient, LLMService

### 🃏 CardService (`cards.py`)
**Role**: Handles card listing and filtering operations  
**Responsibilities**:
- Intelligent deck name resolution
- Field auto-detection
- LLM-based card filtering
- Natural deck ordering (top/bottom)
- Card data preparation and formatting

**Methods**:
- `list_cards()` - Main card listing with filtering/ordering
- `_resolve_deck_and_find_notes()` - Deck resolution logic
- `_prepare_card_data()` - Note to card data conversion
- `_apply_llm_filtering()` - LLM-based filtering
- `_apply_natural_ordering()` - Position-based ordering

**Dependencies**: AnkiConnectClient, LLMService

### 📚 DeckService (`decks.py`)
**Role**: Handles deck-related operations  
**Responsibilities**:
- Deck listing with statistics
- Deck name retrieval
- Fuzzy deck name matching

**Methods**:
- `list_decks()` - Get all decks with stats
- `get_deck_names()` - Get list of deck names
- `find_best_matching_deck()` - Fuzzy deck matching

**Dependencies**: AnkiConnectClient

## Architecture Benefits

### ✅ **Single Responsibility Principle**
Each service has a single, well-defined purpose:
- CompactionService: Only handles compaction operations
- CardService: Only handles card listing/filtering  
- DeckService: Only handles deck operations
- LogicService: Only orchestrates other services

### ✅ **Improved Maintainability**
- Smaller, focused classes are easier to understand and modify
- Changes to one operation don't affect others
- Clear separation of concerns

### ✅ **Better Testability**
- Each service can be tested independently
- Easier to mock dependencies for unit tests
- More focused test cases

### ✅ **Enhanced Reusability**
- Services can be used independently where needed
- Specialized services can be composed differently
- Clear interfaces for each capability

### ✅ **Backward Compatibility**
- LogicService maintains the same API as before
- No changes needed to existing code using LogicService
- Smooth migration path

## Dependencies

```
LogicService
├── CompactionService
│   ├── AnkiConnectClient
│   └── LLMService
├── CardService  
│   ├── AnkiConnectClient
│   └── LLMService
└── DeckService
    └── AnkiConnectClient
```

## Usage Examples

### Direct Service Usage
```python
# Use specialized services directly
from app.services.cards import CardService
card_service = CardService()
cards = await card_service.list_cards(deck="English", filter_description="business vocabulary")
```

### Facade Usage (Backward Compatible)
```python
# Use through LogicService facade (existing code continues to work)
from app.services.logic import LogicService
logic_service = LogicService()
cards = await logic_service.list_cards(deck="English", filter_description="business vocabulary")
```

## Error Handling

Each service defines its own exception class:
- `CompactionServiceError` - For compaction operations
- `CardServiceError` - For card operations  
- `DeckServiceError` - For deck operations
- `LogicServiceError` - For orchestration errors

The LogicService catches service-specific errors and re-raises them as LogicServiceError for uniform error handling at the API level.
