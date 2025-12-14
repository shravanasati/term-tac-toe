# Term Tac Toe Client

The official client for Term Tac Toe multiplayer game.

## Installation

### From PyPI

```bash
pip install term-tac-toe
```

### From Source

```bash
git clone https://github.com/shravanasati/term-tac-toe.git
cd term-tac-toe/client
uv pip install -e .
```

## Usage

### Default Server

```bash
term-tac-toe
```

Connects to the official server at tac-toe.shravanasati.com

### Custom Server

```bash
term-tac-toe --server <server-ip>
```

Example:

```bash
term-tac-toe --server localhost:8000
```

## Game Instructions

1. Run the client
2. Enter your name
3. Choose to create or join a game room (use room code)
4. Wait for opponent to join
5. Take turns marking the board (X or O)
6. First to three in a row wins!

## Requirements

- Python 3.11+
