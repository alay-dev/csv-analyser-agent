from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from session_manager import session_manager
from graph_builder import create_graph
from logging_config import get_logger
import asyncio

logger = get_logger(__name__)

# Create graph instance
graph = create_graph()

app = FastAPI(title="CSV Analyzer Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class SessionCreateRequest(BaseModel):
    csv_path: str
    session_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    message: str

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    csv_path: str = "sample.csv"

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    logger.info("🚀 Starting CSV Analyzer Agent...")
    try:
        await session_manager.connect()
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Failed to establish database connection: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup database connection on shutdown"""
    logger.info("🛑 Shutting down CSV Analyzer Agent...")
    try:
        await session_manager.disconnect()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")

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
            response_type = last_msg.additional_kwargs.get("message_type", "TEXT")
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
async def get_session_history(session_id: str):
    """Get conversation history for a session from database"""
    try:
        messages = await session_manager.get_session_messages_as_dicts(session_id)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "note": "Stateful mode: Full conversation history retrieved from database"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")
