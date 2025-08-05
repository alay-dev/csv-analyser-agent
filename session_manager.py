from typing import Optional, Dict
from uuid import uuid4
from shared import State
from graph_builder import initialize_state
from logging_config import get_logger
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger(__name__)

def convert_message_to_dict(msg):
    """Convert LangChain message objects to dictionaries with proper role mapping"""
    if hasattr(msg, 'model_dump'):
        msg_dict = msg.model_dump()
    elif hasattr(msg, 'dict'):
        msg_dict = msg.dict()
    else:
        return {"content": str(msg), "role": "unknown"}
    
    # Map LangChain message types to standard roles
    if msg_dict.get('type') == 'human':
        msg_dict['role'] = 'user'
    elif msg_dict.get('type') == 'ai':
        msg_dict['role'] = 'assistant'
    else:
        msg_dict['role'] = msg_dict.get('type', 'unknown')
    
    return msg_dict

class SessionManager:
    def __init__(self):
        # In-memory storage for active sessions (session_id -> csv_path mapping)
        self._active_sessions: Dict[str, str] = {}
        
        # Log initialization
        logger.info("🔧 SessionManager initialized (stateless mode)")
        logger.info("💡 Sessions will be initialized dynamically from CSV files")
        
    async def disconnect(self):
        """Cleanup method for compatibility - no database to disconnect from"""
        logger.info("🧹 SessionManager cleanup (no database connections to close)")
        self._active_sessions.clear()
    
    async def create_session(self, session_id: Optional[str] = None, csv_path: str = "sample.csv") -> str:
        """Create a new session identifier and associate it with a CSV path"""
        logger.info(f"📝 Creating new session with CSV: {csv_path}")
        
        if not session_id:
            session_id = str(uuid4())
            logger.info(f"🆔 Generated new session ID: {session_id}")
        else:
            logger.info(f"🆔 Using provided session ID: {session_id}")
        
        # Store the session-to-CSV mapping
        self._active_sessions[session_id] = csv_path
        logger.info(f"✅ Session created successfully: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str, csv_path: str = "sample.csv") -> Optional[State]:
        """Initialize and return session state dynamically based on CSV file"""
        logger.info(f"🔍 Initializing session state: {session_id}")
        
        try:
            # Get CSV path for this session, or use provided/default
            session_csv_path = self._active_sessions.get(session_id, csv_path)
            logger.info(f"📁 Using CSV file: {session_csv_path}")
            
            # Initialize fresh state from CSV
            logger.info("🔄 Initializing fresh session state from CSV...")
            state = initialize_state(session_csv_path)
            state["session_id"] = session_id
            logger.info("✅ Session state initialized successfully")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize session {session_id}: {str(e)}")
            raise
    
    async def get_session_with_messages(self, session_id: str, messages: list, csv_path: str = "sample.csv") -> Optional[State]:
        """Initialize session state and add provided messages with proper roles"""
        logger.info(f"🔍 Initializing session state with messages: {session_id}")
        
        try:
            # Get CSV path for this session, or use provided/default
            session_csv_path = self._active_sessions.get(session_id, csv_path)
            logger.info(f"📁 Using CSV file: {session_csv_path}")
            
            # Initialize fresh state from CSV
            logger.info("🔄 Initializing fresh session state from CSV...")
            state = initialize_state(session_csv_path)
            state["session_id"] = session_id
            
            # Add the provided messages to the state
            if messages:
                logger.info(f"📝 Adding {len(messages)} messages to session state")
                # Ensure messages are properly formatted with roles
                formatted_messages = []
                for msg in messages:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        if msg["role"] == "user":
                            formatted_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant" or msg["role"] == "ai":
                            # Create AIMessage with additional_kwargs for type information
                            additional_kwargs = {}
                            if "type" in msg:
                                additional_kwargs["type"] = msg["type"]
                            formatted_messages.append(AIMessage(content=msg["content"], additional_kwargs=additional_kwargs))
                        else:
                            # For other message types, preserve the original message object if it exists
                            formatted_messages.append(msg)
                    else:
                        # If it's already a message object, keep it as is
                        formatted_messages.append(msg)
                
                state["messages"].extend(formatted_messages)
                logger.info(f"✅ Added messages to state. Total messages: {len(state['messages'])}")
            
            logger.info("✅ Session state initialized successfully with messages")
            return state
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize session {session_id} with messages: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, state: State) -> bool:
        """No-op for stateless mode - state is not persisted"""
        logger.info(f"💡 Session update skipped (stateless mode): {session_id}")
        logger.info(f"📊 Session has {len(state.get('messages', []))} messages")
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Remove session from active sessions tracking"""
        logger.info(f"🗑️ Deleting session: {session_id}")
        
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.info(f"✅ Session deleted successfully: {session_id}")
            return True
        else:
            logger.warning(f"⚠️ Session not found for deletion: {session_id}")
            return False
    
    async def list_sessions(self, limit: int = 100) -> list:
        """List active sessions"""
        logger.info(f"📋 Listing active sessions (limit: {limit})")
        
        sessions = []
        for session_id, csv_path in list(self._active_sessions.items())[:limit]:
            sessions.append({
                "session_id": session_id,
                "csv_path": csv_path,
                "created_at": None,  # Not tracked in stateless mode
                "updated_at": None   # Not tracked in stateless mode
            })
        
        logger.info(f"✅ Found {len(sessions)} active sessions")
        return sessions
    
    async def get_session_messages_as_dicts(self, session_id: str, csv_path: str = "sample.csv") -> list:
        """Get session messages converted to dictionaries with proper role mapping"""
        logger.info(f"📋 Getting messages for session: {session_id}")
        
        session_state = await self.get_session(session_id, csv_path)
        if not session_state:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return []
        
        messages = []
        for msg in session_state.get("messages", []):
            messages.append(convert_message_to_dict(msg))
        
        logger.info(f"✅ Retrieved {len(messages)} messages for session {session_id}")
        return messages

# Global session manager instance
session_manager = SessionManager()