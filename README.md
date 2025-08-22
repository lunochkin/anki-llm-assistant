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
- Python 3.8+

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd anki-llm-assistant

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your OpenAI API key and model preferences
```

### Usage
```bash
# Start the assistant
python src/agent.py

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

This project follows a **spec-first development approach**:

- **`/specs/`** - Complete specifications and schemas
- **`/src/`** - Implementation code
- **`/tests/` - Test suites and golden test data**

## Development

For developers interested in contributing or understanding the system architecture:

- **Specifications**: See `/specs/` for complete system specifications
- **Implementation**: Check `/src/` for the actual code
- **Testing**: Review `/tests/` for test coverage and examples

## Contributing

1. Read the specifications in `/specs/`
2. Follow the established patterns and invariants
3. Add tests for new functionality
4. Ensure all invariants are satisfied

## License

[Add your license information here]

## Support

For questions, issues, or contributions, please check the specifications in `/specs/` or open an issue in the repository.
