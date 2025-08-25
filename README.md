# Anki LLM Assistant

A conversational AI assistant that helps you browse and explore your Anki flashcards through natural language chat.

## What It Does

The Anki LLM Assistant lets you interact with your Anki collection using plain English. Instead of navigating through menus and clicking buttons, you can simply ask questions like:

- "Show me my French decks"
- "What cards are in my vocabulary deck?"
- "List my recent study materials"

## Features

- **Natural Language Interface**: Chat with your Anki collection using conversational language
- **Deck Browsing**: Discover and explore your available study decks
- **Card Preview**: View card content without opening Anki
- **Smart Limits**: Automatically manages data display to keep responses focused
- **Privacy-First**: Only shows card content when explicitly requested

## Quick Start

### Prerequisites
- Anki installed and running
- AnkiConnect add-on installed
- Python 3.11+

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd anki-llm-assistant

# Install dependencies
uv sync

# Set up environment variables
cp env.example .env
# Edit .env with your OpenAI API key and model preferences
```

### Usage
```bash
# Start the assistant
python src/gen/main.py

# Or use the CLI
python src/gen/cli.py --query "Show my decks"

# Or run specific tasks
python tasks.py
```

## Example Conversations

**User**: "What decks do I have?"
**Assistant**: Shows your available decks with note counts

**User**: "Show me 5 cards from my French vocabulary deck"
**Assistant**: Displays 5 cards with front/back content

**User**: "How many cards are in my math deck?"
**Assistant**: Provides deck statistics and summary

## Architecture

This project follows a **spec-first development approach** with a **tiered architecture**:

- **`/specs/`** - Tier-1: Complete specifications, schemas, and configuration
- **`/src/core/`** - Tier-2: Business logic and services
- **`/src/gen/`** - Tier-3: Generated interfaces and entry points
- **`/tests/`** - Test suites and golden test data

### Key Principles
- **Single source of truth**: All specifications live in `/specs/`
- **No hidden logic**: Tier-3 is generated from Tier-2, which implements Tier-1
- **Executable specs**: Configuration files drive system behavior

## Anki Service Modes

The assistant supports two modes for accessing Anki data:

### Mock Mode (Default)
- **Purpose**: Development, testing, and demonstration
- **Data**: Hardcoded sample decks and cards
- **Configuration**: Set `anki: mock` in `specs/implementation.yaml`
- **Use case**: When you don't have Anki running or want to test the interface

### AnkiConnect Mode
- **Purpose**: Real Anki data access
- **Data**: Live data from your Anki collection
- **Requirements**: 
  - Anki running with AnkiConnect add-on installed
  - AnkiConnect enabled and accessible at `http://127.0.0.1:8765`
- **Configuration**: Set `anki: anki_connect` in `specs/implementation.yaml`
- **Use case**: Production use with real Anki data

### Switching Between Modes

The system automatically supports both mock and real Anki services. You can switch between them using environment variables or CLI parameters:

#### Environment Variable Control
```bash
# Use mock service (default)
export ANKI_MODE=mock

# Use real AnkiConnect service
export ANKI_MODE=anki_connect

# Test the service
python -m src.app.cli test-service
```

#### CLI Override
```bash
# Override to mock mode
python -m src.app.cli test-service --mode mock

# Override to AnkiConnect mode
python -m src.app.cli test-service --mode anki_connect
```

#### Configuration
The `specs/implementation.yaml` only contains the Anki URL - the mode is controlled at runtime:
```yaml
adapters:
  anki_url: http://127.0.0.1:8765  # AnkiConnect API endpoint
```

**Note**: No code regeneration is needed to switch between modes. The system automatically detects and uses the appropriate service based on your environment configuration.

#### Running the Assistant
```bash
# Interactive chat
python -m src.app.cli chat

# Test queries
python -m src.app.cli test
```

## Development

For developers interested in contributing or understanding the system architecture:

- **Specifications**: See `/specs/` for complete system specifications
- **Core Logic**: Check `/src/core/` for business logic and services
- **Generated Code**: Review `/src/gen/` for interfaces and entry points
- **Testing**: Review `/tests/` for test coverage and examples

### Development Workflow
1. **Spec first**: Modify files in `/specs/` to define behavior
2. **Implement**: Add business logic in `/src/core/`
3. **Generate**: Create interfaces in `/src/gen/` (or auto-generate later)
4. **Test**: Ensure implementation matches specifications

### Development Tasks
```bash
# Generate Pydantic models from YAML schemas
invoke generate-models

# Generate models and run tests
invoke generate-and-test

# Run golden tests
invoke test-golden

# Test CLI
invoke cli-query
```

## Contributing

1. Read the specifications in `/specs/`
2. Follow the established patterns and invariants
3. Add tests for new functionality
4. Ensure all invariants are satisfied

## License

MIT

## Support

For questions, issues, or contributions, please check the specifications in `/specs/` or open an issue in the repository.
