"""
Supabase Authentication Integration for Streamlit

This module provides authentication verification for the Streamlit app.
It checks for valid Supabase sessions from the Next.js landing page.
"""

import streamlit as st
from supabase import create_client, Client
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
LANDING_PAGE_URL = os.getenv("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError(
        "Missing Supabase credentials. Please set NEXT_PUBLIC_SUPABASE_URL and "
        "NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env file."
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_session_from_cookies() -> Optional[Dict[str, Any]]:
    """
    Extract Supabase session from browser cookies.

    Supabase stores auth tokens in cookies like:
    - sb-<project-id>-auth-token

    Returns:
        dict: Session data if valid, None otherwise
    """
    # Streamlit doesn't have direct cookie access in the same way Next.js does
    # We'll use query parameters as a fallback for passing session tokens
    # This is a simplified version - production should use proper session management

    # Try to get access_token from query params (passed from Next.js redirect)
    query_params = st.query_params
    access_token = query_params.get("access_token", None)

    if access_token:
        try:
            # Verify the token with Supabase
            user = supabase.auth.get_user(access_token)
            if user:
                return {
                    "access_token": access_token,
                    "user": user.user
                }
        except Exception as e:
            st.error(f"Token verification failed: {e}")
            return None

    return None


def check_authentication() -> Optional[Dict[str, Any]]:
    """
    Check if user is authenticated via Supabase.

    Returns:
        dict: User data if authenticated, None otherwise
    """
    session = get_session_from_cookies()

    if session:
        return session["user"]

    return None


def require_authentication():
    """
    Enforce authentication for the Streamlit app.
    Redirects to landing page login if not authenticated.

    Usage:
        Add this at the top of your main.py:

        from core.auth import require_authentication

        # Check auth before rendering app
        user = require_authentication()
    """
    user = check_authentication()

    if not user:
        # User not authenticated - show redirect message
        st.markdown("""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            text-align: center;
            padding: 2rem;
        ">
            <h1 style="
                font-size: 3rem;
                background: linear-gradient(to right, #9333ea, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
            ">
                💊 pilldreams
            </h1>
            <p style="font-size: 1.25rem; color: #6b7280; margin-bottom: 2rem;">
                Authentication Required
            </p>
            <p style="color: #9ca3af; margin-bottom: 2rem;">
                Please log in through the landing page to access the dashboard.
            </p>
            <a href="{}" style="
                display: inline-block;
                padding: 0.75rem 2rem;
                background: linear-gradient(to right, #9333ea, #3b82f6);
                color: white;
                text-decoration: none;
                border-radius: 0.5rem;
                font-weight: 600;
                transition: opacity 0.2s;
            " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                Go to Login →
            </a>
        </div>
        """.format(f"{LANDING_PAGE_URL}/login"), unsafe_allow_html=True)

        st.stop()

    return user


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user data.

    Returns:
        dict: User data including email, id, etc.
    """
    return check_authentication()


def logout():
    """
    Log out the current user and redirect to landing page.
    """
    st.markdown(f"""
    <script>
        window.location.href = "{LANDING_PAGE_URL}/login";
    </script>
    """, unsafe_allow_html=True)
    st.stop()
