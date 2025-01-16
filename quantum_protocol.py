from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
import base64
import secrets
import hashlib
import hmac
import time
import logging
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuantumProtocol:
    def __init__(self):
        self.public_keys = {}  # Store public keys for clients
        self.message_cache = {}  # Prevent replay attacks
        self.session_keys = {}  # Store session-specific keys
        self.key_timestamps = {}  # Track when keys were created
        self.manager = None  # Will be set from main.py
        
    def set_manager(self, manager):
        """Set the connection manager"""
        self.manager = manager

    async def generate_key(self, alice_ws, bob_ws):
        try:
            # Generate unique session identifier
            session_id = base64.urlsafe_b64encode(os.urandom(24)).decode('utf-8')
            
            # Generate a single shared key for both parties
            shared_key = os.urandom(32)  # Generate one key instead of separate keys
            
            # Store the same key for both participants
            self.session_keys[session_id] = {
                alice_ws.client_id: shared_key,
                bob_ws.client_id: shared_key  # Use the same key
            }
            
            # Update timestamp
            self.key_timestamps[session_id] = time.time()
            
            logger.info(f"Sending shared key to participants")
            # Send the same key and session ID to both participants
            for ws in [alice_ws, bob_ws]:
                await ws.send_json({
                    "type": "key_generated",
                    "session_id": session_id,
                    "encryption_key": base64.b64encode(shared_key).decode('utf-8'),
                    "message": "Key exchange completed"
                })
            
            logger.info(f"Key exchange completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error in generate_key: {str(e)}")
            return False

    async def _rotate_keys(self, session_id, alice_ws, bob_ws):
        """Generate new keys and session ID"""
        try:
            # Generate new session ID
            new_session_id = base64.urlsafe_b64encode(os.urandom(24)).decode('utf-8')
            logger.info(f"Generated new session ID: {new_session_id}")
            
            # Generate single new shared key
            new_shared_key = os.urandom(32)
            
            # Store new shared key
            self.session_keys[new_session_id] = {
                alice_ws.client_id: new_shared_key,
                bob_ws.client_id: new_shared_key  # Same key for both participants
            }
            
            # Update timestamp for new session
            self.key_timestamps[new_session_id] = time.time()
            
            # Remove old session
            if session_id in self.session_keys:
                del self.session_keys[session_id]
            if session_id in self.key_timestamps:
                del self.key_timestamps[session_id]
            
            logger.info(f"Sending new shared key to participants")
            # Send new key and session ID to both participants
            for ws in [alice_ws, bob_ws]:
                await ws.send_json({
                    "type": "key_rotation",
                    "session_id": new_session_id,
                    "encryption_key": base64.b64encode(new_shared_key).decode('utf-8'),
                    "message": "Key and session rotated"
                })
            
            logger.info(f"Keys and session rotated successfully")
            return True
        except Exception as e:
            logger.error(f"Error rotating keys: {str(e)}")
            return False

    async def check_and_rotate_keys(self, session_id):
        """Check if keys need rotation and rotate if necessary"""
        try:
            if session_id in self.key_timestamps:
                current_time = time.time()
                last_rotation = self.key_timestamps[session_id]
                
                # Strict 20-second check
                if current_time - last_rotation >= 20:
                    logger.info(f"Time to rotate keys for session {session_id}")
                    if session_id in self.session_keys:
                        participants = list(self.session_keys[session_id].keys())
                        if len(participants) == 2 and self.manager:
                            alice_ws = self.manager.active_connections.get(participants[0])
                            bob_ws = self.manager.active_connections.get(participants[1])
                            
                            if alice_ws and bob_ws:
                                logger.info("Starting key rotation...")
                                success = await self._rotate_keys(session_id, alice_ws, bob_ws)
                                if success:
                                    logger.info("Key rotation completed")
                                    # Update timestamp only after successful rotation
                                    self.key_timestamps[session_id] = current_time
        except Exception as e:
            logger.error(f"Error in check_and_rotate_keys: {str(e)}")

    async def broadcast_message(self, sender_ws, receiver_ws, message):
        try:
            # Get session ID from the message
            session_id = message.get('session_id')
            if not session_id or session_id not in self.session_keys:
                raise ValueError("Invalid or expired session")

            # Verify the sender has access to this session
            if sender_ws.client_id not in self.session_keys[session_id]:
                raise ValueError("Sender not authorized for this session")

            await receiver_ws.send_json({
                "type": "encrypted_message",
                "from": sender_ws.client_id,
                "message": message.get('message'),
                "session_id": session_id
            })
            return True
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
            return False

    async def store_public_key(self, client_id, public_key_str):
        try:
            # Store the public key for the client
            self.public_keys[client_id] = public_key_str
            return True
        except Exception as e:
            logger.error(f"Error storing public key: {str(e)}")
            return False

    def is_replay_attack(self, message_id, timestamp):
        # Check if message is too old (more than 5 minutes)
        message_time = datetime.fromtimestamp(timestamp / 1000.0)
        if datetime.now() - message_time > timedelta(minutes=5):
            return True
            
        # Check if message ID has been seen before
        if message_id in self.message_cache:
            return True
            
        # Store message ID in cache
        self.message_cache[message_id] = timestamp
        
        # Clean old messages from cache
        self._clean_message_cache()
        
        return False

    def _clean_message_cache(self):
        current_time = datetime.now()
        expired_messages = [
            msg_id for msg_id, timestamp in self.message_cache.items()
            if current_time - datetime.fromtimestamp(timestamp / 1000.0) > timedelta(minutes=30)
        ]
        for msg_id in expired_messages:
            del self.message_cache[msg_id] 

    def cleanup_old_sessions(self):
        """Remove old session keys periodically"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id in self.session_keys:
            if current_time - self.session_keys[session_id].get('created_at', 0) > 3600:  # 1 hour expiry
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.session_keys[session_id] 