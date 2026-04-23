# protoproxy

Fast, lightweight protocol translation hub. Normalizes any supported protocol into a canonical format and re-serializes it out.

---

## Overview

protoproxy sits between a reverse proxy and one or more backend services. Incoming requests — regardless of source protocol — are normalized into a shared canonical Python dict. From there, protoproxy routes and re-serializes into whatever protocol the target backend speaks.

New protocols are two files: an input module that normalizes into the canonical dict, and an output module that translates back out. The core stays untouched.

Currently supports HTTPS, MCP, and WebSocket.

```
                                     +------------------------------------+
                                     |             protoproxy             |
                                     |                                    |
                                     |  +------------------------------+  |
                                     |  |   auth (bearer validation)   |  |
                                     |  +------------------------------+  |
                                     |                                    |
               +----------+          |  +----------+     +-------------+  |
 Internet <--> |  Nginx   | <------> |  |  https   |     |  canonical  |  |
  (HTTPS)      |  :443    |          |  |  input/  |<--->|    dict     |  |
               |   TLS    |          |  |  output  |     |             |  |
               |Rate limit|          |  +----------+     +-------------+  |
               |          |          |                          ^         |
               +----------+          |                          |         |
                                     |                          v         |
                                     |                   +-------------+  |
                                     |                   |     mcp     |  |
                                     |                   |   input/    |  |
                                     |                   |   output    |  |
                                     |                   +-------------+  |
                                     |                          |         |
                                     +--------------------------+---------+
                                                                |
                                                                v
                                                        +---------------+
                                                        |  MCP Server   |
                                                        |    :9090      |
                                                        +---------------+
```

protoproxy doesn't replace your reverse proxy — it complements it. Nginx handles TLS termination and rate limiting; protoproxy handles bearer token validation and protocol translation. Only clean, decrypted traffic reaches protoproxy.

---

## How It Works

1. Reverse proxy terminates TLS, enforces rate limits, and forwards decrypted traffic to protoproxy
2. The matching input module (e.g. `https_input.py`) receives the request on its configured port
3. `auth.py` validates the bearer token against the server-side secret; unauthorized requests are rejected before any further processing
4. The input module normalizes the authorized request into a canonical Python dict — a neutral intermediate format every module understands
5. `router.py` consults `config.json` to pick the target output module and dispatches the canonical dict to it
6. The output module (e.g. `mcp_output.py`) translates the canonical dict into the target protocol and forwards it to the backend service
7. The response travels back through the same chain in reverse — backend → output module → canonical dict → input module → reverse proxy → client

---

## Configuration

protoproxy is configured via `config.json`. Secrets (tokens, keys) go in `.env` and are never committed.

```json
{
  "inputs": {
    "https": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8080
    },
    "mcp": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8090
    },
    "websocket": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8081
    }
  },
  "outputs": {
    "https": {
      "enabled": true,
      "endpoint": "http://localhost:9080"
    },
    "mcp": {
      "enabled": true,
      "endpoint": "http://localhost:9090"
    },
    "websocket": {
      "enabled": true,
      "endpoint": "ws://localhost:9081"
    }
  },
  "router": {
    "default_output": "mcp"
  }
}
```

### `inputs`

Each key under `inputs` is a protocol name, mapped to a listening socket. The protocol name must match a module in `src/protoproxy/modules/` (e.g. `https` → `https_input.py`).

| Key | Type | Description |
|---|---|---|
| `enabled` | bool | Whether to start this input on launch |
| `host` | str | Interface to bind to. `0.0.0.0` for all interfaces, `127.0.0.1` for localhost only |
| `port` | int | Port to listen on |

### `outputs`

Each key under `outputs` is a protocol name, mapped to a backend destination protoproxy dials when routing. `endpoint` is a full URL because an output needs scheme + host + port + (optional) path — unlike inputs, which only need a bind target.

| Key | Type | Description |
|---|---|---|
| `enabled` | bool | Whether to make this output available to the router |
| `endpoint` | str | Full URL of the backend service (e.g. `http://localhost:9090`, `ws://localhost:9081`) |

### `router`

| Key | Type | Description |
|---|---|---|
| `default_output` | str | Protocol name to route to when no explicit output is specified by the request |

---

## Authentication

protoproxy authenticates incoming requests with a server-side bearer token. Every input module invokes `modules/auth.py` before normalizing the request; requests without a valid `Authorization: Bearer <token>` header are rejected with `401 Unauthorized`.

The token lives in `.env` (never committed) and is loaded into the process environment at startup. Comparison is timing-safe (via `hmac.compare_digest`) to avoid leaking the secret through response-time side channels.

**Setup:**

1. Generate a token:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Copy `.env.example` to `.env` and paste the value:
   ```
   PROTOPROXY_BEARER_TOKEN=your-generated-token-here
   ```
3. Share the token out-of-band with any client that needs access.

**Client usage:**

```bash
curl -H "Authorization: Bearer <your-token>" https://your-host/path
```

Rotating the token is a matter of editing `.env` and restarting protoproxy. Clients using the old token get `401` immediately.

---

## Installation

```bash
pip install protoproxy
```

Or from source:

```bash
git clone https://github.com/geomux/protoproxy.git
cd protoproxy
pip install -e .
```

## Quick Start

```bash
python -m protoproxy
```

protoproxy loads `config.json` from the working directory and starts one listener per enabled input. With the default config, that's `0.0.0.0:8080` for HTTPS, `0.0.0.0:8090` for MCP, and `0.0.0.0:8081` for WebSocket.

---

## Supported Protocols

- HTTPS
- MCP
- WebSocket

---

## Contributing

Issues and PRs welcome. To add a new protocol, open an issue first to discuss the canonical dict contract before writing code.

## License

MIT
