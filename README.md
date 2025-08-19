# Anki LLM Assistant

A **local-first chat assistant for Anki** that talks to **AnkiConnect (localhost:8765)** and uses an **LLM only for intent parsing + compacting example sentences**. Ship a minimal but production-quality project with tests and a clean README.

## 🎯 What It Does

This assistant helps you manage your Anki cards by:

- **Compacting long example sentences** to 10-16 words while preserving target vocabulary
- **Rolling back changes** to restore original examples
- **Natural language commands** - just chat with it like a human!

## 🚀 Features

- **Local-only**: No data leaves your machine
- **Safety rails**: Preview changes before applying, automatic backups
- **Smart LLM integration**: Uses LLM only for intent parsing and sentence compaction
- **Web interface**: Clean chat UI with confirmation buttons
- **CLI support**: Command-line interface for automation
- **Health monitoring**: Real-time status of AnkiConnect and LLM services

## 🛠️ Tech Stack

- **Python 3.11+** with FastAPI
- **AnkiConnect** for Anki integration
- **OpenAI API** (or compatible) for LLM operations
- **Modern web UI** with vanilla JavaScript
- **Comprehensive testing** with pytest

## 📋 Prerequisites

1. **Anki** installed and running
2. **AnkiConnect** add-on installed in Anki
3. **Python 3.11+** installed
4. **OpenAI API key** (or compatible service)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install -e .
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with your settings
OPENAI_API_KEY=sk-your-actual-api-key-here
LLM_MODEL=gpt-4o-mini
ANKI_URL=http://127.0.0.1:8765
```

### 3. Start Anki & AnkiConnect

1. Open Anki
2. Ensure AnkiConnect add-on is enabled
3. AnkiConnect runs on `http://127.0.0.1:8765`

### 4. Run the Assistant

```bash
# Start the web server
.venv/bin/python -m uvicorn app.main:app --reload

# Open in browser
http://127.0.0.1:8000
```

## 💬 Usage Examples

### Chat Commands

Try these natural language commands in the web interface:

```
Compact examples in deck 'News B2', preview 5, apply 30
```

```
Rollback compacted examples in 'News B2'
```

### CLI Usage

```bash
# Preview compaction
python -m app.main --cli compact "News B2" Example 5 30

# Rollback changes
python -m app.main --cli rollback "News B2" Example
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model to use |
| `ANKI_URL` | `http://127.0.0.1:8765` | AnkiConnect endpoint |
| `DEFAULT_EXAMPLE_FIELD` | `Example` | Default field to compact |
| `DEFAULT_PREVIEW_COUNT` | `5` | Default preview items |
| `DEFAULT_LIMIT` | `30` | Default max notes to process |
| `MAX_BATCH_SIZE` | `100` | Maximum batch size |
| `RATE_LIMIT_MS` | `250` | Rate limit between LLM calls |

### AnkiConnect Setup

1. **Install AnkiConnect**:
   - Download from [AnkiWeb](https://ankiweb.net/shared/info/2055492159)
   - Install in Anki: Tools → Add-ons → Install from file

2. **Verify Installation**:
   - Restart Anki
   - Check Tools → Add-ons for "AnkiConnect"
   - Default port: 8765

## 🏗️ Project Structure

```
anki-llm-assistant/
├── app/
│   ├── main.py              # FastAPI app + CLI entry point
│   ├── routers/
│   │   ├── chat.py         # Chat endpoints
│   │   └── ops.py          # Direct operations
│   ├── services/
│   │   ├── anki.py         # AnkiConnect client
│   │   ├── llm.py          # LLM service
│   │   └── logic.py        # Business logic orchestration
│   ├── models/
│   │   └── schemas.py      # Pydantic models
│   ├── templates/
│   │   └── index.html      # Chat interface
│   └── static/
│       ├── app.js          # Frontend logic
│       └── styles.css      # Styling
├── tests/
│   └── test_logic.py       # Service tests
├── pyproject.toml          # Project configuration
├── env.example             # Environment template
└── README.md               # This file
```

## 🔒 Safety Features

- **Preview mode**: See changes before applying
- **Automatic backups**: Original examples saved to `{field}_Original`
- **Confirmation tokens**: Secure tokens for applying changes
- **Batch limits**: Configurable limits to prevent overwhelming
- **Rate limiting**: Gentle on LLM API
- **Tagging**: Notes tagged with `compact_examples` for tracking

## 🧪 Testing

```bash
# Install test dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## 🔍 API Endpoints

### Chat Interface
- `POST /chat/` - Natural language commands

### Direct Operations
- `POST /ops/compact/preview` - Preview compaction
- `POST /ops/compact/apply` - Apply with token
- `POST /ops/rollback` - Rollback changes

### Utility
- `GET /health` - Health check
- `GET /decks` - List available decks
- `GET /` - Web interface

## 🚨 Troubleshooting

### Common Issues

1. **AnkiConnect Connection Failed**
   - Ensure Anki is running
   - Check AnkiConnect add-on is enabled
   - Verify port 8765 is accessible

2. **LLM API Errors**
   - Check `OPENAI_API_KEY` in `.env`
   - Verify API key has sufficient credits
   - Check model name compatibility

3. **No Notes Found**
   - Verify deck name (case-sensitive)
   - Check field name exists in note type
   - Ensure notes have content in specified field

4. **Permission Errors**
   - Check Anki is not in read-only mode
   - Verify add-on permissions

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Enhancements

- [ ] **Multiple LLM providers** (Claude, Gemini, local models)
- [ ] **Batch processing** with progress bars
- [ ] **Custom note types** support
- [ ] **Export/import** functionality
- [ ] **Scheduled operations** with cron-like syntax
- [ ] **Advanced filtering** and search
- [ ] **Statistics dashboard** for deck analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Anki** team for the amazing spaced repetition software
- **AnkiConnect** developers for the powerful API
- **FastAPI** team for the modern Python web framework
- **OpenAI** for the LLM capabilities

---

**Happy studying with Anki! 🎓**

*This assistant helps you focus on learning by managing the technical details of your Anki cards.*
