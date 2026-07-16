import asyncio
import json
import logging
import uvicorn
import warnings
import os
from pathlib import Path


from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment variables from .env file BEFORE importing agent
load_dotenv()

# Import agent after loading environment variables
# pylint: disable=wrong-import-position
from biometric_agent.agent import root_agent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, # Default to INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Suppress noisy loggers
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("google_adk").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Suppress Pydantic serialization warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

PORT = 8080
APP_NAME = "alpha-drone"
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
# ========================================
# Phase 1: Application Initialization (once at startup)
# ========================================

app = FastAPI()

# Add CORS middleware to allow WebSocket connections from any origin
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define your session service
session_service = InMemorySessionService()

# Define your runner
runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)

# ========================================
# WebSocket Endpoint
# ========================================


@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    proactivity: bool = True,
    affective_dialog: bool = False,
) -> None:
    """WebSocket endpoint for bidirectional streaming with ADK.

    Args:
        websocket: The WebSocket connection
        user_id: User identifier
        session_id: Session identifier
        proactivity: Enable proactive audio (native audio models only)
        affective_dialog: Enable affective dialog (native audio models only)
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {user_id}/{session_id}")

    # ========================================
    # Phase 2: Session Initialization (once per streaming session)
    # ========================================

    # Automatically determine response modality based on model architecture
    # Native audio models (containing "native-audio" in name)
    # ONLY support AUDIO response modality.
    # Half-cascade models support both TEXT and AUDIO;
    # we default to TEXT for better performance.

    model_name = root_agent.model
    is_native_audio = "native-audio" in model_name.lower() or "live" in model_name.lower()

    if is_native_audio:
        # Native audio models require AUDIO response modality
        # with audio transcription
        response_modalities = ["AUDIO"]

        # Build RunConfig with optional proactivity and affective dialog
        # These features are only supported on native audio models
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=response_modalities,
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            session_resumption=types.SessionResumptionConfig(),
            proactivity=(
                types.ProactivityConfig(proactive_audio=True) if proactivity else None
            ),
            enable_affective_dialog=affective_dialog if affective_dialog else None,
        )
        logger.info(f"Model Config: {model_name} (Modalities: {response_modalities}, Proactivity: {proactivity})")
    else:
        # Half-cascade models support TEXT response modality
        # for faster performance
        response_modalities = ["TEXT"]
        run_config = None
        logger.info(f"Model Config: {model_name} (Modalities: {response_modalities})")

    # Get or create session (handles both new sessions and reconnections)
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
    
    #REPLACE_LIVE_REQUEST

#REPLACE_SORT_RESPONSE


# Serve Static Files (Fallback for SPA)
# Mount static files if directory exists
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
    print(f"Serving static files from: {FRONTEND_DIST}")
else:
    print(f"Warning: Frontend build not found at {FRONTEND_DIST}")
    print("Please run 'npm run build' in the frontend directory.")

if __name__ == "__main__":
    # Run uvicorn programmatically
    uvicorn.run(app, host="0.0.0.0", port=PORT)