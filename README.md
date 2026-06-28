# simplex-ai-bot

A privacy-respecting AI assistant bot for [SimpleX Chat](https://simplex.chat), powered by [Groq](https://console.groq.com) and Llama 3.

SimpleX is the only messaging network with no user identifiers — no phone number, no email, no username. This bot runs entirely on your own machine. The only data that leaves it is the message text sent to Groq's API.

---

## What it does

- Answers questions in natural language using Llama 3.1 (via Groq's free API)
- Maintains a rolling conversation history (last 20 messages) per contact, so the AI has context across a conversation
- Handles only direct messages — ignores group chats and non-text content
- Supports `/reset` to wipe a contact's history and start fresh
- Built-in anti-loop guard: skips echoes of its own replies
- No database, no external storage — all state lives in memory

---

## Requirements

- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier is sufficient)
- SimpleX Chat CLI installed and running as a WebSocket server

---

## Setup

**1. Install the SimpleX Chat CLI:**

```bash
curl -o- https://raw.githubusercontent.com/simplex-chat/simplex-chat/stable/install.sh | bash
```

**2. Start it as a WebSocket server** (create a profile on the first run):

```bash
simplex-chat -p 5225
```

**3. In a second terminal, open the interactive CLI, enable auto-accept, and copy your address:**

```bash
simplex-chat
/auto_accept on
/address
/exit
```

Share the address with anyone you want to reach the bot.

**4. Clone this repo and install dependencies:**

```bash
git clone https://github.com/JnanaSrota/simplex-ai-bot
cd simplex-ai-bot
pip install -r requirements.txt
```

**5. Set your Groq API key:**

```bash
export GROQ_API_KEY="gsk_..."
```

---

## Run

```bash
python ai_bot.py
```

Leave the WebSocket server (`simplex-chat -p 5225`) running in the other terminal. The bot connects to it, waits for messages, and replies through Groq.

---

## Usage

Connect to the bot's address via your SimpleX app and send any message.

| Input | Response |
|---|---|
| Any text | AI reply with conversation context |
| `/reset` | Clears your conversation history with the bot |

---

## How it works

```
SimpleX app  →  simplex-chat CLI (WebSocket :5225)  →  ai_bot.py  →  Groq API
                          ↑                                  |
                          └──────────────────────────────────┘
                                   (reply via WebSocket)
```

The bot connects directly to the CLI's WebSocket API. When a `newChatItems` event arrives, it appends the message to that contact's rolling history, calls Groq asynchronously with the last 20 messages as context, and sends the reply back using `@{contact_name} <text>`. An anti-loop guard tracks the last sent message per contact and skips it if it echoes back as incoming.

---

## Dependencies

| Package | Purpose |
|---|---|
| [`websockets`](https://pypi.org/project/websockets/) | WebSocket connection to the SimpleX CLI |
| [`groq`](https://pypi.org/project/groq/) | Async Groq API client (Llama 3.1 8B Instant) |

---

## License

MIT
