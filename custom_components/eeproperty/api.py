"""API client for eeProperty washing machine system."""
import asyncio
import logging

import aiohttp

from .const import (
    APP_VERSION,
    HEADER_APP_VERSION,
    HEADER_REQUESTED_WITH,
    HEADER_TOKEN,
    LOGIN_API_URL,
    REQUESTED_WITH,
    VESTA_API_URL,
)
from .models import Activity, LoginResponse, Machine, TokenResponse, User

_LOGGER = logging.getLogger(__name__)


class EePropertyApiClient:
    """API client for eeProperty."""

    def __init__(
        self,
        code: str,
        pin: str,
        session: aiohttp.ClientSession,
        token: str | None = None,
        user_id: int | None = None,
        user_label: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._code = code
        self._pin = pin
        self._session = session
        self._token = token
        self._user_id = user_id
        self._user_label = user_label

    def _get_headers(self, include_token: bool = True) -> dict[str, str]:
        """Get standard headers for API requests."""
        headers = {
            HEADER_APP_VERSION: APP_VERSION,
            HEADER_REQUESTED_WITH: REQUESTED_WITH,
        }
        if include_token and self._token:
            headers[HEADER_TOKEN] = self._token
        return headers

    async def login(self) -> bool:
        """Step 1: Login with code and PIN to get user ID."""
        try:
            async with self._session.post(
                f"{LOGIN_API_URL}/api/v3/mobile/user/login",
                json={"code": self._code, "pin": self._pin},
                headers=self._get_headers(include_token=False),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    login_response = LoginResponse.from_dict(data)
                    if login_response.status == 0:
                        self._user_id = login_response.user_id
                        self._user_label = login_response.user_label
                        _LOGGER.debug("Login successful for user %s", self._user_label)
                        return True
                _LOGGER.error("Login failed with status %s", response.status)
                return False
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during login")
            return False
        except aiohttp.ClientError as err:
            _LOGGER.error("Error during login: %s", err)
            return False

    async def send_security_code(self) -> bool:
        """Step 2: Request security code to be sent."""
        if not self._user_id:
            _LOGGER.error("Cannot send security code: not logged in")
            return False

        try:
            async with self._session.post(
                f"{LOGIN_API_URL}/api/v3/mobile/user/send-security-code",
                json={"userId": str(self._user_id)},
                headers=self._get_headers(include_token=False),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == 0:
                        _LOGGER.debug("Security code sent successfully")
                        return True
                _LOGGER.error("Failed to send security code with status %s", response.status)
                return False
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout sending security code")
            return False
        except aiohttp.ClientError as err:
            _LOGGER.error("Error sending security code: %s", err)
            return False

    async def verify_security_code(self, security_code: str) -> bool:
        """Step 3: Verify security code and get authentication token."""
        if not self._user_id:
            _LOGGER.error("Cannot verify security code: not logged in")
            return False

        try:
            async with self._session.post(
                f"{LOGIN_API_URL}/api/v3/mobile/user/security-code",
                json={"userId": str(self._user_id), "securityCode": security_code},
                headers=self._get_headers(include_token=False),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token_response = TokenResponse.from_dict(data)
                    if token_response.status == 0:
                        self._token = token_response.token
                        _LOGGER.debug("Authentication successful, token received")
                        return True
                _LOGGER.error("Security code verification failed with status %s", response.status)
                return False
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout verifying security code")
            return False
        except aiohttp.ClientError as err:
            _LOGGER.error("Error verifying security code: %s", err)
            return False

    async def get_user_data(self) -> User | None:
        """Get user data including balance."""
        if not self.is_authenticated:
            _LOGGER.error("Cannot get user data: not authenticated")
            return None

        try:
            async with self._session.get(
                f"{LOGIN_API_URL}/api/v3/mobile/user/refresh-data",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == 0:
                        return User.from_dict(data["user"])
                _LOGGER.error("Failed to get user data: %s", response.status)
                return None
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting user data")
            return None
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting user data: %s", err)
            return None

    async def validate_token(self) -> bool:
        """Validate that the stored token is still working."""
        if not self.is_authenticated:
            return False

        try:
            async with self._session.get(
                f"{LOGIN_API_URL}/api/v3/mobile/user/refresh-data",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == 0
                return False
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return False

    async def get_machines(self) -> list[Machine]:
        """Get list of washing machines."""
        if not self.is_authenticated:
            _LOGGER.error("Cannot get machines: not authenticated")
            return []

        try:
            async with self._session.get(
                f"{VESTA_API_URL}/api/v3/mobile/machines",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    machines_data = data.get("machines", [])
                    return [Machine.from_dict(m) for m in machines_data]
                _LOGGER.error("Failed to get machines: %s", response.status)
                return []
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting machines")
            return []
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting machines: %s", err)
            return []

    async def get_uses(self, length: int = 20) -> list[Activity]:
        """Get recent usage history."""
        if not self.is_authenticated:
            _LOGGER.error("Cannot get uses: not authenticated")
            return []

        try:
            async with self._session.get(
                f"{VESTA_API_URL}/api/v3/mobile/uses",
                params={"length": length},
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    activities_data = data.get("activities", [])
                    return [Activity.from_dict(a) for a in activities_data]
                _LOGGER.error("Failed to get uses: %s", response.status)
                return []
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting uses")
            return []
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting uses: %s", err)
            return []

    @property
    def user_id(self) -> int | None:
        """Return the user ID."""
        return self._user_id

    @property
    def user_label(self) -> str | None:
        """Return the user label."""
        return self._user_label

    @property
    def is_authenticated(self) -> bool:
        """Return whether client is authenticated."""
        return self._token is not None
