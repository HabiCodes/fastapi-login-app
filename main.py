import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# Enable CORS so your local HTML file can connect smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Database Connection Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:RhHhQnCivrwsCZAEDtXDibvxhNGWPipK@kodama.proxy.rlwy.net:48226/railway")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Create the messages table automatically if it doesn't exist
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            sender_id INT NOT NULL,
            receiver_id INT NOT NULL,
            message_text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

# 2. Live Connection Manager Matrix
class ConnectionManager:
    def __init__(self):
        # Maps user_id to their active live WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_private_message(self, message: str, receiver_id: int):
        if receiver_id in self.active_connections:
            await self.active_connections[receiver_id].send_text(message)

manager = ConnectionManager()

# 3. HTTP Route: Check DB Status
@app.get("/")
def read_root():
    return {"status": "online", "message": "WhatsApp Backend is fully functional! 🚀"}

# 4. HTTP Route: Fetch Historical Chat Logs
@app.get("/history/{user_a}/{user_b}")
def get_chat_history(user_a: int, user_b: int):
    conn = get_db_connection()
    cur = conn.cursor()
    # Pulls all previous conversations between these two users in order
    cur.execute("""
        SELECT sender_id, receiver_id, message_text, timestamp 
        FROM messages 
        WHERE (sender_id = %s AND receiver_id = %s) 
           OR (sender_id = %s AND receiver_id = %s)
        ORDER BY timestamp ASC;
    """, (user_a, user_b, user_b, user_a))
    history = cur.fetchall()
    cur.close()
    conn.close()
    return history

# 5. WebSocket Route: Real-Time Live Traffic
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    user_id = int(user_id)
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Wait for incoming payload string from user's screen
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            receiver_id = int(payload["receiver_id"])
            message_text = payload["message"]

            # Save the message right into Postgres
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO messages (sender_id, receiver_id, message_text) 
                VALUES (%s, %s, %s);
            """, (user_id, receiver_id, message_text))
            conn.commit()
            cur.close()
            conn.close()

            # Instantly forward message to the receiver if they are online
            outgoing_payload = json.dumps({
                "sender_id": user_id,
                "message": message_text
            })
            await manager.send_private_message(outgoing_payload, receiver_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
