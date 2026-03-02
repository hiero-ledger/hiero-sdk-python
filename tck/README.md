# TCK JSON-RPC Server

The TCK (Technology Compatibility Kit) JSON-RPC server provides a standardized interface for testing and validating Hiero SDK implementations.

## Quick Start

Start the server with default settings:

```bash
python -m tck
```

The server will start on `localhost:8544` by default.

## Configuration

### Custom Port Configuration

You can configure the server using environment variables:

- **`TCK_PORT`**: Server port (default: `8544`, valid range: 1-65535)
- **`TCK_HOST`**: Server host (default: `localhost`)

### Examples

**Run on a custom port:**

```bash
TCK_PORT=9000 python -m tck
```

**Run on a different host:**

```bash
TCK_HOST=0.0.0.0 TCK_PORT=8080 python -m tck
```

**Run with both custom host and port:**

```bash
TCK_HOST=127.0.0.1 TCK_PORT=3000 python -m tck
```

## Requirements

The TCK server requires Flask. Install it using:

```bash
pip install -e ".[tck]"
```

## Server Details

- **Protocol**: JSON-RPC 2.0
- **Endpoint**: `POST /`
- **Content-Type**: `application/json`
- **Default URL**: `http://localhost:8544`


## Error Handling

The server validates:
- Port must be a valid integer between 1 and 65535
- Content-Type must be `application/json`
- Requests must conform to JSON-RPC 2.0 specification
