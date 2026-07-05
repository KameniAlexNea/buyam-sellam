"""Helper utilities for KSell Entreprise."""

import json
import random
from typing import Any, Dict, List, Optional


def generate_token(length: int = 6) -> str:
    """Generate a random verification token."""
    return "".join(random.choices("0123456789", k=length))


def parse_json_response(
    response_text: str, keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Parse JSON string into a dictionary, optionally filtering by keys."""
    try:
        data = json.loads(response_text)
        if keys:
            return {k: data.get(k) for k in keys}
        return data
    except (json.JSONDecodeError, TypeError):
        return {}


def format_fortune(value: float) -> str:
    """Format fortune value for display."""
    return f"{value:,.2f} FCFA"


def format_quantity(value: int) -> str:
    """Format quantity for display."""
    return f"{value:,}"


def validate_email(email: str) -> bool:
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[-1]


def validate_username(username: str) -> bool:
    """Validate username meets minimum length."""
    return len(username) >= 5


def validate_password(password: str) -> bool:
    """Validate password meets minimum length."""
    return len(password) >= 8


def get_country_list() -> List[Dict[str, str]]:
    """Get list of countries (sample data)."""
    return [
        {"value": "CM", "text": "Cameroon", "group": "Africa"},
        {"value": "SN", "text": "Senegal", "group": "Africa"},
        {"value": "CI", "text": "Ivory Coast", "group": "Africa"},
        {"value": "BF", "text": "Burkina Faso", "group": "Africa"},
        {"value": "ML", "text": "Mali", "group": "Africa"},
        {"value": "TG", "text": "Togo", "group": "Africa"},
        {"value": "BJ", "text": "Benin", "group": "Africa"},
        {"value": "NE", "text": "Niger", "group": "Africa"},
        {"value": "GN", "text": "Guinea", "group": "Africa"},
        {"value": "FR", "text": "France", "group": "Europe"},
        {"value": "US", "text": "United States", "group": "North America"},
        {"value": "CA", "text": "Canada", "group": "North America"},
        {"value": "BR", "text": "Brazil", "group": "South America"},
        {"value": "JP", "text": "Japan", "group": "Asia"},
        {"value": "CN", "text": "China", "group": "Asia"},
        {"value": "IN", "text": "India", "group": "Asia"},
        {"value": "AU", "text": "Australia", "group": "Oceania"},
        {"value": "GB", "text": "United Kingdom", "group": "Europe"},
        {"value": "DE", "text": "Germany", "group": "Europe"},
        {"value": "NG", "text": "Nigeria", "group": "Africa"},
    ]


def get_gender_options() -> List[str]:
    """Get gender options."""
    return ["Male", "Female"]


def get_profile_options() -> List[str]:
    """Get profile type options."""
    return ["Entrepreneur", "Investor", "Speculator", "Trader"]


def get_market_location_options() -> List[Dict[str, Any]]:
    return [
        {
            "id": "lieu_1",
            "name": "Central Market",
            "min_qty": 50,
            "max_qty": 200,
            "tax_rate": 0.05,
        },
        {
            "id": "lieu_2",
            "name": "North Market",
            "min_qty": 30,
            "max_qty": 150,
            "tax_rate": 0.08,
        },
        {
            "id": "lieu_3",
            "name": "South Market",
            "min_qty": 40,
            "max_qty": 180,
            "tax_rate": 0.06,
        },
        {
            "id": "lieu_4",
            "name": "Commercial Zone",
            "min_qty": 100,
            "max_qty": 500,
            "tax_rate": 0.03,
        },
        {
            "id": "lieu_5",
            "name": "Free Port",
            "min_qty": 200,
            "max_qty": 1000,
            "tax_rate": 0.02,
        },
    ]


def get_tool_options() -> List[Dict[str, Any]]:
    return [
        {"id": "outil_1", "name": "Transport Truck", "cost": 5000, "capacity": 100},
        {"id": "outil_2", "name": "Warehouse", "cost": 10000, "capacity": 500},
        {"id": "outil_3", "name": "Transport Boat", "cost": 15000, "capacity": 1000},
        {"id": "outil_4", "name": "Cargo Plane", "cost": 50000, "capacity": 5000},
        {"id": "outil_5", "name": "Van", "cost": 2000, "capacity": 50},
    ]


def get_card_options() -> List[Dict[str, Any]]:
    return [
        {
            "id": "carte_1",
            "name": "Gold Card",
            "description": "Sales boost",
            "value": 100,
            "price": 5000,
        },
        {
            "id": "carte_2",
            "name": "Silver Card",
            "description": "Tax reduction",
            "value": 50,
            "price": 2500,
        },
        {
            "id": "carte_3",
            "name": "Bronze Card",
            "description": "Starting bonus",
            "value": 25,
            "price": 1000,
        },
        {
            "id": "carte_4",
            "name": "Diamond Card",
            "description": "VIP market access",
            "value": 200,
            "price": 10000,
        },
        {
            "id": "carte_5",
            "name": "Emerald Card",
            "description": "Double production",
            "value": 150,
            "price": 7500,
        },
    ]


def get_dish_options() -> List[Dict[str, Any]]:
    """Get dish options."""
    return [
        {"name": "Rice", "profile": "Staple"},
        {"name": "Pasta", "profile": "Staple"},
        {"name": "Fufu", "profile": "Traditional"},
        {"name": "Yam", "profile": "Tuber"},
        {"name": "Corn", "profile": "Cereal"},
    ]


def get_product_dish_options() -> List[Dict[str, Any]]:
    """Get product-dish combination options."""
    return [
        {"dish": "Rice", "product": "Rice", "percentage": 0.8},
        {"dish": "Pasta", "product": "Pasta", "percentage": 0.7},
        {"dish": "Fufu", "product": "Cassava", "percentage": 0.9},
        {"dish": "Yam", "product": "Yam", "percentage": 0.85},
        {"dish": "Corn", "product": "Corn", "percentage": 0.75},
    ]


def get_penalty_options() -> List[Dict[str, Any]]:
    return [
        {"id": "sanction_1", "name": "Warning", "amount": 0},
        {"id": "sanction_2", "name": "Light Fine", "amount": 1000},
        {"id": "sanction_3", "name": "Medium Fine", "amount": 5000},
        {"id": "sanction_4", "name": "Heavy Fine", "amount": 20000},
        {"id": "sanction_5", "name": "Temp Suspension", "amount": 50000},
    ]


def get_constraint_options() -> List[Dict[str, Any]]:
    """Get constraint options."""
    return [
        {"id": "constraint_1", "name": "None", "description": "No constraint"},
        {
            "id": "constraint_2",
            "name": "Minimum 50 units",
            "description": "Minimum quantity required",
        },
        {
            "id": "constraint_3",
            "name": "Maximum 200 units",
            "description": "Maximum quantity allowed",
        },
        {
            "id": "constraint_4",
            "name": "Reserved for professionals",
            "description": "Only entrepreneurs can sell",
        },
    ]
