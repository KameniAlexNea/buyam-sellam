# buyam-sellam

A business simulation / marketplace game built with Gradio (Python).

## Game Overview

KSell Entreprise is a marketplace simulation game where players:
- Register accounts with country, birth date, and gender
- Roll dice (2d6) to determine market conditions
- Trade products in dynamic markets with taxes and quantities
- Manage tools, cards, and fortune
- Compete with other players in a simulated economy

## Project Structure

```
KSell-Entreprise-Gradio/
├── main.py                  # Entry point - Gradio app
├── requirements.txt         # Python dependencies
├── model/                   # Core game logic models
│   ├── des.py              # Dice (2d6 rolling)
│   ├── joueur.py           # Player model
│   ├── marche.py           # Market model
│   ├── message.py          # Communication messages
│   ├── produit.py          # Product wrapper
│   ├── serveur_message.py  # Server messages
│   └── table.py            # Game table
├── pojo/                    # Data transfer objects
│   ├── carte.py            # Card
│   ├── contrainte.py       # Constraint
│   ├── lieu_vente.py       # Sales location
│   ├── outil.py            # Tool
│   ├── plat.py             # Dish
│   ├── produit.py          # Product
│   ├── produit_plat.py     # Product-Dish combo
│   ├── publication.py      # Publication
│   ├── sanction.py         # Penalty
│   └── user.py             # User
├── services/                # Business logic services
│   ├── api_service.py      # API communication
│   ├── game_service.py     # Game state management
│   └── user_service.py     # User management
├── utils/                   # Utilities
│   ├── constants.py        # App constants
│   ├── helpers.py          # Helper functions
│   └── random_utils.py     # Random number utilities
└── views/                   # Gradio UI pages
    ├── login_page.py       # Login page
    ├── register_page.py    # Registration page
    ├── game_page.py        # Main game page
    ├── market_page.py      # Market/trading page
    ├── profile_page.py     # Profile management
    └── verification_page.py # Email verification
```

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Game Mechanics

### Dice Rolling
- Two dice (1-6 each) determine market conditions
- Total range: 2-12
- Higher rolls = better market conditions

### Markets
- Each market has a location with min/max quantity range
- Tax rate applied to total quantity
- Players can pass through or sell in markets

### Player Economy
- Fortune: Player's wealth
- Cards: Collectible game cards
- Subscribers: Social network followers
- Competitions: Number of games played
- Stars: Achievement rating
