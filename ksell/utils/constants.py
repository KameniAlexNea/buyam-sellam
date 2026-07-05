"""Application constants for KSell Entreprise."""

APP_NAME = "KSell Entreprise"
BASE_URL = "http://127.0.0.1:3001"
IMAGE_FOLDER = "/resources/img/"
VIEW_PATH = "/views/"
ICON_PATH = "/resources/icon/"

# Validation rules
MIN_USERNAME_LENGTH = 5
MIN_PASSWORD_LENGTH = 8

# Game constants
DICE_MIN = 1
DICE_MAX = 6
MIN_FORTUNE = 0.0
DEFAULT_TAX_RATE = 0.1

# API endpoints
LOGIN_ENDPOINT = "/users/login"
SIGNUP_ENDPOINT = "/users/signup"
VERIFICATION_ENDPOINT = "/users/signup/verification"
COUNTRIES_URL = "https://trial.mobiscroll.com/content/countries.json"

# Game states
STATE_LOGIN = "login"
STATE_REGISTER = "register"
STATE_VERIFIED = "verified"
STATE_GAME = "game"
STATE_MARKET = "market"
STATE_PROFILE = "profile"
