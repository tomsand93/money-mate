"""
Authentication module using Supabase Auth
Handles user registration, login, password reset, and session management
"""
import os
from functools import wraps
from flask import session, redirect, url_for, flash, request
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseAuth:
    def __init__(self):
        """Initialize Supabase client for authentication"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Missing Supabase credentials! "
                "Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env file"
            )

        self.client: Client = create_client(supabase_url, supabase_key)

    def sign_up(self, email: str, password: str) -> tuple[bool, str, dict]:
        """
        Register a new user

        Args:
            email: User's email
            password: User's password

        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            response = self.client.auth.sign_up({
                'email': email,
                'password': password
            })

            if response.user:
                logger.info(f"New user registered: {email}")
                return True, "Registration successful! Please check your email to confirm your account.", response.user
            else:
                return False, "Registration failed. Please try again.", None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sign up error: {error_msg}")

            # Handle common errors
            if 'already registered' in error_msg.lower():
                return False, "This email is already registered. Please log in instead.", None
            elif 'invalid email' in error_msg.lower():
                return False, "Invalid email address.", None
            elif 'password' in error_msg.lower():
                return False, "Password must be at least 6 characters.", None
            else:
                return False, f"Registration failed: {error_msg}", None

    def sign_in(self, email: str, password: str) -> tuple[bool, str, dict]:
        """
        Sign in an existing user

        Args:
            email: User's email
            password: User's password

        Returns:
            Tuple of (success, message, session_data)
        """
        try:
            response = self.client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })

            if response.session:
                # Store session in Flask session
                session['user_id'] = response.user.id
                session['email'] = response.user.email
                session['access_token'] = response.session.access_token
                session['refresh_token'] = response.session.refresh_token

                logger.info(f"User logged in: {email}")
                return True, "Login successful!", response.session

            return False, "Login failed. Please try again.", None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sign in error: {error_msg}")

            if 'invalid' in error_msg.lower() or 'credentials' in error_msg.lower():
                return False, "Invalid email or password.", None
            elif 'email not confirmed' in error_msg.lower():
                return False, "Please confirm your email address first.", None
            else:
                return False, f"Login failed: {error_msg}", None

    def sign_out(self) -> tuple[bool, str]:
        """
        Sign out the current user

        Returns:
            Tuple of (success, message)
        """
        try:
            # Sign out from Supabase
            self.client.auth.sign_out()

            # Clear Flask session
            session.clear()

            logger.info("User logged out")
            return True, "Logged out successfully"

        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            # Clear session anyway
            session.clear()
            return True, "Logged out"

    def reset_password_request(self, email: str) -> tuple[bool, str]:
        """
        Send password reset email

        Args:
            email: User's email

        Returns:
            Tuple of (success, message)
        """
        try:
            self.client.auth.reset_password_for_email(email)
            return True, "Password reset email sent! Check your inbox."

        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            # Don't reveal if email exists or not (security)
            return True, "If that email exists, a password reset link has been sent."

    def update_password(self, new_password: str) -> tuple[bool, str]:
        """
        Update user password

        Args:
            new_password: New password

        Returns:
            Tuple of (success, message)
        """
        try:
            self.client.auth.update_user({
                'password': new_password
            })
            return True, "Password updated successfully!"

        except Exception as e:
            logger.error(f"Password update error: {str(e)}")
            return False, f"Password update failed: {str(e)}"

    def get_current_user(self) -> dict:
        """
        Get current authenticated user from session

        Returns:
            User data dict or None
        """
        user_id = session.get('user_id')
        if not user_id:
            return None

        return {
            'id': user_id,
            'email': session.get('email')
        }

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return 'user_id' in session and 'access_token' in session

    def refresh_session(self) -> bool:
        """
        Refresh the authentication session

        Returns:
            True if refresh successful, False otherwise
        """
        refresh_token = session.get('refresh_token')
        if not refresh_token:
            return False

        try:
            response = self.client.auth.refresh_session(refresh_token)

            if response.session:
                # Update session tokens
                session['access_token'] = response.session.access_token
                session['refresh_token'] = response.session.refresh_token
                return True

            return False

        except Exception as e:
            logger.error(f"Session refresh error: {str(e)}")
            return False


# Global auth instance
auth = SupabaseAuth()


# Decorator for routes that require authentication
def login_required(f):
    """
    Decorator to protect routes that require authentication

    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "This is protected"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth.is_authenticated():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# Decorator for routes that require unauthenticated users (login/signup pages)
def guest_only(f):
    """
    Decorator for routes that should only be accessible to non-authenticated users

    Usage:
        @app.route('/login')
        @guest_only
        def login_route():
            return render_template('login.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if auth.is_authenticated():
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
