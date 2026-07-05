"""API Service for KSell Entreprise.

Handles communication with the backend API (or simulated backend for Gradio).
In Gradio mode, this simulates API calls locally since we don't have a running backend.
"""

import random
import string
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from ksell.pojo.user import User
from ksell.utils.constants import (
    BASE_URL,
    COUNTRIES_URL,
    LOGIN_ENDPOINT,
    SIGNUP_ENDPOINT,
    VERIFICATION_ENDPOINT,
)
from ksell.utils.helpers import generate_token, get_country_list


class ApiService:
    """Simulated API service for Gradio (no real backend needed).

    In a real deployment, this would make HTTP requests to the Node.js backend.
    For Gradio, we simulate the backend locally with in-memory storage.
    """

    def __init__(self):
        self._base = BASE_URL
        self._token = ""
        self._users_db: Dict[str, Dict[str, Any]] = {}  # pseudo -> user data
        self._verification_tokens: Dict[str, str] = {}  # email -> token
        self._countries: List[Dict[str, str]] = get_country_list()

    # ---- Country data ----

    def get_countries(self) -> List[Dict[str, str]]:
        """Get list of countries."""
        return self._countries

    # ---- Authentication ----

    def login(self, pseudo: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Simulate user login.

        Returns:
            Tuple of (success, message, user)
        """
        if pseudo in self._users_db:
            user_data = self._users_db[pseudo]
            if user_data.get("password") == password:
                if not user_data.get("is_verified", False):
                    return False, "Account not verified. Please verify your email first.", None
                user = User(**{k: v for k, v in user_data.items() if k in User.__dataclass_fields__})
                self._token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                return True, "Login successful!", user
            else:
                return False, "Invalid password.", None
        else:
            # For demo purposes, auto-create and login
            user = User(
                username=pseudo,
                email=f"{pseudo}@demo.com",
                balance=10000.0,
                is_verified=True,
            )
            self._users_db[pseudo] = asdict(user)
            self._users_db[pseudo]["password"] = password
            self._token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            return True, "Login successful! (Demo account created)", user

    def register(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Simulate user registration.

        Args:
            data: Dict with pseudo, password, mail, pays, dateNaissance, sexe, profil

        Returns:
            Tuple of (success, message)
        """
        pseudo = data.get("pseudo", "")
        password = data.get("password", "")
        mail = data.get("mail", "")
        country = data.get("pays", "")
        birth_date = data.get("dateNaissance", "")
        gender = data.get("sexe", "")
        profile = data.get("profil", "Entrepreneur")

        # Validation
        if not pseudo or len(pseudo) < 5:
            return False, "Username must be at least 5 characters."
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters."
        if "@" not in mail:
            return False, "Invalid email address."
        if not country:
            return False, "Please select a country."

        # Check if user already exists
        if pseudo in self._users_db:
            return False, f"User '{pseudo}' already exists."

        # Generate verification token
        token = generate_token(6)
        self._verification_tokens[mail] = token

        # Create user
        user = User(
            username=pseudo,
            email=mail,
            country=country,
            birth_date=birth_date,
            gender=gender,
            profile=profile,
            balance=10000.0,
            is_verified=False,
        )
        self._users_db[pseudo] = asdict(user)
        self._users_db[pseudo]["password"] = password

        return True, f"Registration successful! Verification code sent to {mail}: {token}"

    def verify(self, token: str) -> Tuple[bool, str]:
        """Simulate email verification.

        Args:
            token: Verification code

        Returns:
            Tuple of (success, message)
        """
        # Find user with matching token
        for email, stored_token in self._verification_tokens.items():
            if stored_token == token:
                # Find and update user
                for pseudo, user_data in self._users_db.items():
                    if user_data.get("email") == email:
                        user_data["is_verified"] = True
                        del self._verification_tokens[email]
                        return True, f"Account verified successfully! You can now log in as '{pseudo}'."
                return False, "Verification failed. Token not found."

        return False, "Invalid verification code. Please try again."

    def get_user(self, pseudo: str) -> Optional[User]:
        if pseudo in self._users_db:
            return User(**{k: v for k, v in self._users_db[pseudo].items() if k in User.__dataclass_fields__})
        return None

    def update_user(self, user: User) -> bool:
        if user.username in self._users_db:
            self._users_db[user.username] = asdict(user)
            return True
        return False

    def get_all_users(self) -> List[User]:
        return [User(**{k: v for k, v in data.items() if k in User.__dataclass_fields__}) for data in self._users_db.values()]
