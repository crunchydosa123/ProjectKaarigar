"""
Simple authentication helper for cross-origin requests
Checks session first, then falls back to X-User-ID header
"""
from flask import session, request

def get_user_from_session():
    """Get user ID from session or X-User-ID header"""
    # First try session (works for same-origin)
    user_id = session.get('user_id')
    
    # Fallback to header (works for cross-origin)
    if not user_id:
        user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        raise ValueError("No user session found. Please login first.")
    
    return user_id
