"""Data models for eeproperty API."""
from dataclasses import dataclass
from typing import Literal

MachineType = Literal["WASHER", "DRYER"]
MachineState = Literal["DEACTIVATED", "ACTIVATED", "ERROR"]
PricingType = Literal["TIME"]


@dataclass
class Machine:
    """Represents a washing machine or dryer."""

    type: MachineType
    number: int
    state: MachineState
    pricing: PricingType
    cost_per_cycle: int
    room: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Machine":
        """Create a Machine from API response dictionary."""
        return cls(
            type=data["type"],
            number=data["number"],
            state=data["state"],
            pricing=data["pricing"],
            cost_per_cycle=data["costPerCycle"] / 100,
            room=data.get("room"),
        )

    @property
    def friendly_state(self) -> str:
        """Return a user-friendly state name."""
        if self.state == "DEACTIVATED":
            return "Available"
        elif self.state == "ACTIVATED":
            return "Occupied"
        elif self.state == "ERROR":
            return "Unavailable"
        return self.state

    @property
    def type_name(self) -> str:
        """Return a user-friendly type name."""
        return "Washing Machine" if self.type == "WASHER" else "Dryer"


@dataclass
class UserPreferences:
    """User notification preferences."""

    notif_email_charging_end: bool
    notif_email_credit: bool
    notif_email_cycle_end: bool
    notif_email_info: bool
    notif_email_subscription_fees: bool
    notif_push_charging_end: bool
    notif_push_credit: bool
    notif_push_cycle_end: bool
    notif_push_info: bool
    notif_push_subscription_fees: bool
    notif_sms_credit: bool
    notif_sms_cycle_end: bool
    two_factors_auth: bool

    @classmethod
    def from_dict(cls, data: dict) -> "UserPreferences":
        """Create UserPreferences from API response dictionary."""
        return cls(
            notif_email_charging_end=data["notifEmailChargingEnd"],
            notif_email_credit=data["notifEmailCredit"],
            notif_email_cycle_end=data["notifEmailCycleEnd"],
            notif_email_info=data["notifEmailInfo"],
            notif_email_subscription_fees=data["notifEmailSubscriptionFees"],
            notif_push_charging_end=data["notifPushChargingEnd"],
            notif_push_credit=data["notifPushCredit"],
            notif_push_cycle_end=data["notifPushCycleEnd"],
            notif_push_info=data["notifPushInfo"],
            notif_push_subscription_fees=data["notifPushSubscriptionFees"],
            notif_sms_credit=data["notifSmsCredit"],
            notif_sms_cycle_end=data["notifSmsCycleEnd"],
            two_factors_auth=data["twoFactorsAuth"],
        )


@dataclass
class UserServices:
    """User available services."""

    vesta: bool
    volta: bool

    @classmethod
    def from_dict(cls, data: dict) -> "UserServices":
        """Create UserServices from API response dictionary."""
        return cls(
            vesta=data["vesta"],
            volta=data["volta"],
        )


@dataclass
class User:
    """Represents a user account."""

    id: int
    number: str
    first_name: str
    last_name: str
    language: str
    unlimited_balance: bool
    balance: int
    secret: str
    address: str
    email: str
    mobile: str
    migrated: bool
    services: UserServices
    preferences: UserPreferences

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create a User from API response dictionary."""
        return cls(
            id=data["id"],
            number=data["number"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            language=data["language"],
            unlimited_balance=data["unlimitedBalance"],
            balance=data["balance"] / 100,
            secret=data["secret"],
            address=data["address"],
            email=data["email"],
            mobile=data["mobile"],
            migrated=data["migrated"],
            services=UserServices.from_dict(data["services"]),
            preferences=UserPreferences.from_dict(data["preferences"]),
        )

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"


@dataclass
class Activity:
    """Represents a usage activity."""

    date: str
    command: str
    activity: str
    machine: str
    duration: int
    cost: int
    balance: int

    @classmethod
    def from_dict(cls, data: dict) -> "Activity":
        """Create an Activity from API response dictionary."""
        return cls(
            date=data["date"],
            command=data["command"],
            activity=data["activity"],
            machine=data["machine"],
            duration=data["duration"],
            cost=data["cost"],
            balance=data["balance"],
        )


@dataclass
class LoginResponse:
    """Response from login API."""

    status: int
    message: str
    user_id: int
    user_label: str

    @classmethod
    def from_dict(cls, data: dict) -> "LoginResponse":
        """Create LoginResponse from API response dictionary."""
        return cls(
            status=data["status"],
            message=data["message"],
            user_id=data["userId"],
            user_label=data["userLabel"],
        )


@dataclass
class TokenResponse:
    """Response from security code verification API."""

    status: int
    message: str
    token: str
    token_refresh_interval: int

    @classmethod
    def from_dict(cls, data: dict) -> "TokenResponse":
        """Create TokenResponse from API response dictionary."""
        return cls(
            status=data["status"],
            message=data["message"],
            token=data["token"],
            token_refresh_interval=data["tokenRefreshInterval"],
        )


@dataclass
class EePropertyData:
    """Data class for coordinator data."""

    machines: list[Machine]
    user: User | None
