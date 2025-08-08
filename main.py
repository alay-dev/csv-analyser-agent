from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from graph_builder import create_graph
from session_manager import session_manager, convert_message_to_dict
from dotenv import load_dotenv
from typing import Optional
from contextlib import asynccontextmanager
import asyncio
import os
from logging_config import setup_logging, get_logger

load_dotenv()

# Set up logging based on environment variable
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(level=log_level, format_style="detailed")
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 FastAPI server starting up...")
    logger.info("💡 Running in stateless mode - sessions initialized from CSV files")
    yield
    # Shutdown
    logger.info("🛑 FastAPI server shutting down...")
    await session_manager.disconnect()

app = FastAPI(lifespan=lifespan)

# Optional CORS middleware if calling from browser or frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create graph once (stateless)
graph = create_graph()

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    csv_path: Optional[str] = "sample.csv"

class SessionCreateRequest(BaseModel):
    csv_path: Optional[str] = "sample.csv"
    session_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    message: str

@app.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """Create a new session"""
    logger.info(f"📝 API request to create session with CSV: {request.csv_path}")
    try:
        session_id = await session_manager.create_session(
            csv_path=request.csv_path,
            session_id=request.session_id
        )
        logger.info(f"✅ Session creation API completed: {session_id}")
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully"
        )
    except Exception as e:
        logger.error(f"❌ Session creation API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        deleted = await session_manager.delete_session(session_id)
        if deleted:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """List all sessions"""
    try:
        sessions = await session_manager.list_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.post("/query")
async def query_chatbot(request: QueryRequest):
    """Process a query for a specific session"""
    logger.info(f"🤖 Processing query: '{request.query[:50]}...' for session: {request.session_id or 'auto-create'}")
    
    try:
        session_id = request.session_id
        
        # If no session_id provided, create a new session
        if not session_id:
            logger.info("🆔 No session ID provided, creating new session")
            session_id = await session_manager.create_session(csv_path=request.csv_path)
        
        # Get current session state (always initializes fresh from CSV)
        # First, create the user message that will be added
        user_message = {"role": "user", "content": request.query}
        
        # Initialize session state with the user message
        current_state = await session_manager.get_session_with_messages(
            session_id, 
            [user_message], 
            csv_path=request.csv_path
        )
        
        # If session doesn't exist in tracking, create it
        if not current_state:
            logger.info(f"🔄 Session {session_id} not found, creating new session")
            session_id = await session_manager.create_session(
                csv_path=request.csv_path,
                session_id=session_id
            )
            current_state = await session_manager.get_session_with_messages(
                session_id, 
                [user_message], 
                csv_path=request.csv_path
            )
        
        if not current_state:
            logger.error(f"❌ Failed to initialize session: {session_id}")
            raise HTTPException(status_code=500, detail="Failed to initialize session")
        
        logger.info(f"📝 Session state initialized with user message. Total messages: {len(current_state['messages'])}")
        
        # Process the query through the graph
        logger.info("🔄 Processing query through graph...")
        updated_state = graph.invoke(current_state)
        logger.info("✅ Graph processing completed")
        
        # Update session in database
        await session_manager.update_session(session_id, updated_state)
        
        # Return response
        if updated_state.get("messages"):
            last_msg = updated_state["messages"][-1]
            response_type = last_msg.additional_kwargs.get("type", "TEXT")
            logger.info(f"✅ Query processed successfully. Response type: {response_type}")
            return {
                "response": last_msg.content,
                "type": response_type,
                "session_id": session_id
            }
        
        logger.warning("⚠️ No messages in updated state, returning default response")
        return {
            "response": "Sorry, I couldn't process your query.",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str, csv_path: Optional[str] = "sample.csv"):
    """Get conversation history for a session (stateless mode - returns fresh state)"""
    try:
        # In stateless mode, we can only return the fresh initialized state
        # No conversation history is persisted
        messages = await session_manager.get_session_messages_as_dicts(session_id, csv_path=csv_path)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "note": "Stateless mode: Only fresh session state returned, no conversation history persisted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")
