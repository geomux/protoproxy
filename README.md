# protoproxy

Fast, lightweight protocol translation hub. Normalizes any supported protocol into a canonical format and re-serializes it out.

---

## Overview

protoproxy sits between a reverse proxy and one or more backend services. Incoming requests — regardless of source protocol — are normalized into a shared canonical Python dict. From there, protoproxy routes and re-serializes into whatever protocol the target backend speaks.

New protocols are two files: an input module that normalizes into the canonical dict, and an output module that translates back out. The core stays untouched.

Currently supports HTTPS and MCP.

```
                                     +------------------------------------+
                                     |             protoproxy             |
                                     |                                    |
               +----------+          |  +----------+     +-------------+  |
 Internet <--> |  Nginx   | <------> |  |  https   |     |  Canonical  |  |
  (HTTPS)      |  :443    |          |  |  input/  |<--->|    dict     |  |
               |Rate limit|          |  |  output  |     |             |  |
               |  Bearer  |          |  +----------+     +-------------+  |
               |  token   |          |                          ^         |
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
                                                        |    :8026      |
                                                        +---------------+
```

protoproxy doesn't replace your reverse proxy — it complements it. Nginx handles TLS termination, rate limiting, and bearer token or API key authentication. Only clean, authorized traffic reaches protoproxy.

---

## How It Works

1. Reverse proxy receives public HTTPS traffic, enforces rate limits and auth, and forwards clean requests to protoproxy
2. `main.py` receives the forwarded request and checks `config.json` to determine the source protocol and target backend
3. `https_input.py` breaks down the incoming request into a canonical Python dict — a neutral intermediate format every module understands
4. `main.py` checks `config.json` for the target port and protocol, then calls the matching output module
5. `mcp_output.py` translates the canonical dict into the target protocol and forwards it to the backend service
6. The response travels back through the same chain in reverse — backend → output module → canonical dict → input module → reverse proxy → client

---

## Configuration

protoproxy is configured via `config.json`. Secrets (tokens, keys) go in `.env` and are never committed.

```json
{
    "PROTOPROXY_HOST": "127.0.0.1",
    "PROTOPROXY_PORT": 8008,
    "LOG_LEVEL": "info",

    "PROXY_HOST": "127.0.0.1",
    "PROXY_PORT": 8008,

    "OUTPUTS": {
        "mcp": {
            "host": "127.0.0.1",
            "port": 8026
        }
    }
}
```

| Key | Type | Description |
|---|---|---|
| `PROTOPROXY_HOST` | str | Interface protoproxy binds to |
| `PROTOPROXY_PORT` | int | Port protoproxy listens on (default `8008`) |
| `LOG_LEVEL` | str | `debug`, `info`, `warning`, `error` |
| `PROXY_HOST` | str | Host of your reverse proxy |
| `PROXY_PORT` | int | Port your reverse proxy forwards to protoproxy |
| `OUTPUTS` | dict | Protocol name → host and port of backend service |

---

## Installation

```bash
pip install protoproxy
```

Or from source:

```bash
git clone https://github.com/YOUR_USERNAME/protoproxy.git
cd protoproxy
pip install -e .
```

## Quick Start

```bash
python -m protoproxy
```

protoproxy will start on `127.0.0.1:8008` by default and load `config.json` from the working directory.

---

## Supported Protocols
| HTTPS |
| MCP |

---

## Contributing

Issues and PRs welcome. To add a new protocol, open an issue first to discuss the canonical dict contract before writing code.

## License

MIT
