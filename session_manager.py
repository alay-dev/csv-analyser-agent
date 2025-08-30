from typing import Optional, Dict
from uuid import uuid4
from datetime import datetime
from shared import State
from graph_builder import initialize_state
from logging_config import get_logger
from langchain_core.messages import HumanMessage, AIMessage
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import json

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

def serialize_state(state: State) -> dict:
    """Serialize State object to dictionary for MongoDB storage"""
    # Handle State as a TypedDict - access keys directly
    serialized = {
        "session_id": state.get("session_id", None),
        "csv_path": state.get("csv_path", ""),
        "thread_id": state.get("thread_id", ""),
        "message_type": state.get("message_type", None),
        "schema": state.get("schema", None),
        "dataframe": None,  # Don't serialize pandas DataFrame
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Serialize messages
    messages = state.get("messages", [])
    for msg in messages:
        msg_dict = convert_message_to_dict(msg)
        serialized["messages"].append(msg_dict)
    
    return serialized

def deserialize_state(data: dict) -> State:
    """Deserialize MongoDB document back to State object"""
    state = {
        "session_id": data.get("session_id", ""),
        "csv_path": data.get("csv_path", ""),
        "thread_id": data.get("thread_id", ""),
        "message_type": data.get("message_type", None),
        "schema": data.get("schema", None),
        "dataframe": None,  # Will be reloaded from CSV
        "messages": []
    }
    
    # Deserialize messages back to LangChain message objects
    for msg_dict in data.get("messages", []):
        if msg_dict.get("role") == "user":
            state["messages"].append(HumanMessage(content=msg_dict.get("content", "")))
        elif msg_dict.get("role") in ["assistant", "ai"]:
            additional_kwargs = {}
            if "type" in msg_dict:
                additional_kwargs["type"] = msg_dict["type"]
            state["messages"].append(AIMessage(content=msg_dict.get("content", ""), additional_kwargs=additional_kwargs))
    
    return state

class SessionManager:
    def __init__(self):
        # MongoDB client placeholders
        self._client: Optional[AsyncIOMotorClient] = None
        self._db = None
        self._sessions_col = None
        
        # Log initialization
        logger.info("🔧 SessionManager initialized (stateful mode)")
        logger.info("💾 Sessions will be persisted to MongoDB")

    async def connect(self):
        """Establish MongoDB connection based on configuration"""
        if self._client:
            logger.info("🔌 MongoDB already connected")
            return

        # Get connection details from config
        url = Config.get_mongodb_url()
        db_name = Config.MONGODB_DATABASE

        # Create client and verify connection
        self._client = AsyncIOMotorClient(url)
        self._db = self._client[db_name]
        self._sessions_col = self._db["sessions"]
        await self._db.command("ping")
        logger.info(f"🔌 Connected to MongoDB database '{db_name}'")
        
    async def disconnect(self):
        """Cleanup and close MongoDB connection"""
        logger.info("🧹 SessionManager cleanup")
        try:
            if self._client:
                self._client.close()
                logger.info("🔌 MongoDB connection closed")
        finally:
            self._client = None
            self._db = None
            self._sessions_col = None
    
    async def create_session(self, csv_path: str, session_id: Optional[str] = None) -> str:
        """Create a new session and persist it to MongoDB"""
        logger.info(f"📝 Creating new session with CSV: {csv_path}")
        
        if not session_id:
            session_id = str(uuid4())
            logger.info(f"🆔 Generated new session ID: {session_id}")
        else:
            logger.info(f"🆔 Using provided session ID: {session_id}")
        
        # Initialize state from CSV
        state = initialize_state(csv_path)
        state["session_id"] = session_id
        
        # Only persist to MongoDB if connected
        if self._sessions_col is not None:
            try:
                # Serialize and store in MongoDB
                session_doc = serialize_state(state)
                await self._sessions_col.insert_one(session_doc)
                logger.info(f"✅ Session created and persisted to MongoDB: {session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to persist to MongoDB: {str(e)}")
                logger.info(f"💡 Session created in memory only: {session_id}")
        else:
            logger.info(f"💡 Session created in memory only (MongoDB not connected): {session_id}")
        
        return session_id
    
    async def get_session(self, session_id: str, csv_path: str = "sample.csv") -> Optional[State]:
        """Retrieve session state from MongoDB"""
        logger.info(f"🔍 Retrieving session state: {session_id}")
        
        # If MongoDB is not connected, we can't retrieve existing sessions
        if self._sessions_col is None:
            logger.info(f"💡 MongoDB not connected, cannot retrieve session: {session_id}")
            return None
        
        try:
            # Try to get existing session from database
            session_doc = await self._sessions_col.find_one({"session_id": session_id})
            
            if session_doc:
                logger.info(f"✅ Found existing session: {session_id}")
                state = deserialize_state(session_doc)
                
                # Reload CSV data since DataFrame can't be serialized
                if not state.get("dataframe") or not state.get("schema"):
                    logger.info("🔄 Reloading CSV data for existing session")
                    from graph_builder import initialize_state
                    fresh_state = initialize_state(state["csv_path"])
                    state["dataframe"] = fresh_state.get("dataframe")
                    state["schema"] = fresh_state.get("schema")
                
                return state
            else:
                logger.info(f"🔄 Session not found: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve session {session_id}: {str(e)}")
            raise
    
    async def get_session_with_messages(self, session_id: str, messages: list, csv_path: str = "sample.csv") -> Optional[State]:
        """Retrieve session state and add provided messages"""
        logger.info(f"🔍 Retrieving session state with messages: {session_id}")
        
        try:
            # Get existing session or create new one
            state = await self.get_session(session_id, csv_path)
            
            if not state:
                logger.info(f"🔄 Session not found, creating new one: {session_id}")
                # Create new session if not found
                await self.create_session(csv_path, session_id)
                # Now get the newly created session
                state = await self.get_session(session_id, csv_path)
                if not state:
                    raise Exception(f"Failed to create session: {session_id}")
            
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
            
            logger.info("✅ Session state retrieved successfully with messages")
            return state
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve session {session_id} with messages: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, state: State) -> bool:
        """Update session state in MongoDB"""
        logger.info(f"💾 Updating session in database: {session_id}")
        
        # If MongoDB is not connected, we can't update sessions
        if self._sessions_col is None:
            logger.info(f"💡 MongoDB not connected, session update skipped: {session_id}")
            return True
        
        try:
            # Serialize the updated state
            session_doc = serialize_state(state)
            session_doc["updated_at"] = datetime.utcnow()
            
            # Update in MongoDB
            result = await self._sessions_col.replace_one(
                {"session_id": session_id},
                session_doc,
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id:
                logger.info(f"✅ Session updated successfully: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ No changes made to session: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update session {session_id}: {str(e)}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from MongoDB"""
        logger.info(f"🗑️ Deleting session: {session_id}")
        
        # If MongoDB is not connected, we can't delete sessions
        if self._sessions_col is None:
            logger.info(f"💡 MongoDB not connected, session deletion skipped: {session_id}")
            return True
        
        try:
            result = await self._sessions_col.delete_one({"session_id": session_id})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Session deleted successfully: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ Session not found for deletion: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete session {session_id}: {str(e)}")
            raise
    
    async def list_sessions(self, limit: int = 100) -> list:
        """List all sessions from MongoDB"""
        logger.info(f"📋 Listing sessions from database (limit: {limit})")
        
        # If MongoDB is not connected, return empty list
        if self._sessions_col is None:
            logger.info(f"💡 MongoDB not connected, returning empty session list")
            return []
        
        try:
            cursor = self._sessions_col.find({}).sort("created_at", -1).limit(limit)
            sessions = []
            
            async for doc in cursor:
                sessions.append({
                    "session_id": doc.get("session_id"),
                    "csv_path": doc.get("csv_path"),
                    "created_at": doc.get("created_at"),
                    "updated_at": doc.get("updated_at"),
                    "message_count": len(doc.get("messages", []))
                })
            
            logger.info(f"✅ Found {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Failed to list sessions: {str(e)}")
            raise
    
    async def get_session_messages_as_dicts(self, session_id: str, csv_path: str = "sample.csv") -> list:
        """Get session messages from MongoDB"""
        logger.info(f"📋 Getting messages for session: {session_id}")
        
        # If MongoDB is not connected, return empty list
        if self._sessions_col is None:
            logger.info(f"💡 MongoDB not connected, returning empty message list for session: {session_id}")
            return []
        
        try:
            session_doc = await self._sessions_col.find_one({"session_id": session_id})
            
            if not session_doc:
                logger.warning(f"⚠️ Session not found: {session_id}")
                return []
            
            messages = session_doc.get("messages", [])
            logger.info(f"✅ Retrieved {len(messages)} messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Failed to get messages for session {session_id}: {str(e)}")
            raise

# Global session manager instance
session_manager = SessionManager()