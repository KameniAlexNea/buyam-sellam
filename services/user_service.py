"""User Service for KSell Entreprise.

Manages user-related operations: registration, login, profile updates.
"""

from typing import Any, Dict, List, Optional, Tuple

from pojo.user import User
from services.api_service import ApiService


class UserService:
    """Handles user authentication and profile management."""

    def __init__(self, api_service: Optional[ApiService] = None):
        self.api = api_service or ApiService()
        self.current_user: Optional[User] = None

    def login(self, pseudo: str, password: str, auto_verify: bool = False) -> Tuple[bool, str, Optional[User]]:
        """Log in a user.

        Args:
            pseudo: Username
            password: Password
            auto_verify: If True and account is unverified, auto-verify for demo

        Returns:
            Tuple of (success, message, user)
        """
        success, message, user = self.api.login(pseudo, password)
        if not success and "not verified" in message.lower() and auto_verify:
            users = self.api.get_all_users()
            for u in users:
                if u.username == pseudo:
                    u.is_verified = True
                    self.api.update_user(u)
                    success, message, user = self.api.login(pseudo, password)
                    break
        if success and user:
            self.current_user = user
        return success, message, user

    def register(
        self,
        pseudo: str,
        password: str,
        mail: str,
        pays: str,
        date_naissance: str,
        sexe: str = "",
        profil: str = "Entrepreneur",
    ) -> Tuple[bool, str]:
        """Register a new user.

        Args:
            pseudo: Username (min 5 chars)
            password: Password (min 8 chars)
            mail: Email address
            pays: Country
            date_naissance: Birth date
            sexe: Gender
            profil: Profile type

        Returns:
            Tuple of (success, message)
        """
        data = {
            "pseudo": pseudo,
            "password": password,
            "mail": mail,
            "pays": pays,
            "dateNaissance": date_naissance,
            "sexe": sexe,
            "profil": profil,
        }
        return self.api.register(data)

    def verify(self, token: str) -> Tuple[bool, str]:
        """Verify a user account with a token.

        Args:
            token: Verification code

        Returns:
            Tuple of (success, message)
        """
        return self.api.verify(token)

    def get_current_user(self) -> Optional[User]:
        """Get the currently logged-in user."""
        return self.current_user

    def update_profile(
        self,
        pseudo: str,
        email: str = None,
        profil: str = None,
        pays: str = None,
    ) -> Tuple[bool, str]:
        """Update user profile.

        Args:
            pseudo: Username
            email: New email
            profil: New profile type
            pays: New country

        Returns:
            Tuple of (success, message)
        """
        if not self.current_user:
            return False, "No user logged in."

        if email:
            self.current_user.email = email
        if profil:
            self.current_user.profil = profil
        if pays:
            self.current_user.pays = pays

        success = self.api.update_user(self.current_user)
        if success:
            return True, "Profile updated successfully!"
        return False, "Failed to update profile."

    def get_countries(self) -> List[Dict[str, str]]:
        """Get list of available countries."""
        return self.api.get_countries()

    def get_all_users(self) -> List[User]:
        """Get all registered users (demo)."""
        return self.api.get_all_users()
