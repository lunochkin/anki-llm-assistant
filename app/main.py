"""Main FastAPI application for Anki LLM Assistant."""

import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from dotenv import load_dotenv

from app.routers import chat, ops
from app.services.anki import AnkiConnectClient
from app.services.llm import LLMService
from app.models.schemas import HealthResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Anki LLM Assistant...")
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    
    logger.info("Environment variables loaded successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Anki LLM Assistant...")


# Create FastAPI app
app = FastAPI(
    title="Anki LLM Assistant",
    description="Local LLM chat assistant for Anki with AnkiConnect integration",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(chat.router)
app.include_router(ops.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check AnkiConnect
        async with AnkiConnectClient() as anki_client:
            anki_connect_available = await anki_client.health_check()
        
        # Check LLM service
        llm_service = LLMService()
        llm_available = await llm_service.health_check()
        
        status = "healthy" if anki_connect_available and llm_available else "degraded"
        
        return HealthResponse(
            status=status,
            anki_connect=anki_connect_available,
            llm=llm_available
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            anki_connect=False,
            llm=False
        )


@app.get("/decks")
async def list_decks():
    """List available Anki decks."""
    try:
        from app.services.logic import LogicService
        logic_service = LogicService()
        decks = await logic_service.list_decks()
        return {"decks": decks}
    except Exception as e:
        logger.error(f"Failed to list decks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list decks")


async def cli_main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m app.main --cli")
        print("Commands:")
        print("  compact <deck> [field] [preview_count] [limit]")
        print("  rollback <deck> [field]")
        print("  list-decks")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "compact":
            if len(sys.argv) < 3:
                print("Usage: compact <deck> [field] [preview_count] [limit]")
                return
            
            deck = sys.argv[2]
            field = sys.argv[3] if len(sys.argv) > 3 else "Example"
            preview_count = int(sys.argv[4]) if len(sys.argv) > 4 else 5
            limit = int(sys.argv[5]) if len(sys.argv) > 5 else 30
            
            from app.services.logic import LogicService
            logic_service = LogicService()
            
            print(f"Previewing compaction for deck '{deck}'...")
            preview = await logic_service.compact_examples(
                deck=deck, field=field, preview_count=preview_count, limit=limit
            )
            
            if preview.count == 0:
                print("No examples found for compaction.")
                return
            
            print(f"\nFound {preview.count} examples to compact:")
            for diff in preview.diffs:
                print(f"\nNote {diff.note_id} (word: '{diff.word}'):")
                print(f"  Old: {diff.old}")
                print(f"  New: {diff.new}")
            
            if preview.needs_confirmation:
                print(f"\nConfirmation token: {preview.confirm_token}")
                print("Use this token to apply the changes.")
        
        elif command == "rollback":
            if len(sys.argv) < 3:
                print("Usage: rollback <deck> [field]")
                return
            
            deck = sys.argv[2]
            field = sys.argv[3] if len(sys.argv) > 3 else "Example"
            
            from app.services.logic import LogicService
            logic_service = LogicService()
            
            print(f"Rolling back compacted examples in deck '{deck}'...")
            result = await logic_service.rollback_compacted(deck, field)
            
            if result.restored == 0:
                print("No examples found to rollback.")
            else:
                print(f"Successfully restored {result.restored} examples.")
        
        elif command == "list-decks":
            from app.services.logic import LogicService
            logic_service = LogicService()
            decks = await logic_service.list_decks()
            if not decks:
                print("No decks found.")
            else:
                print(f"Found {len(decks)} decks:")
                for i, deck in enumerate(decks, 1):
                    deck_id = deck.get("id", "N/A")
                    note_count = deck.get("note_count", 0)
                    example_count = deck.get("example_count", 0)
                    print(f"{i}. {deck['name']} (ID: {deck_id})")
                    print(f"   Notes: {note_count}, Examples: {example_count}")
                    print()
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: compact, rollback, list-decks")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        exit(asyncio.run(cli_main()))
    else:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True
        )
