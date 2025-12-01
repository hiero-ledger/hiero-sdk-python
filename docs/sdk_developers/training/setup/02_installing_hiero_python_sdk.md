## Quick Set-up

### Fork the Hiero Python SDK
Create your GitHub fork, then clone your fork locally and connect it to the upstream repo to make it easy to sync in the future.

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/hiero-sdk-python.git
cd hiero-sdk-python
# Add upstream for future syncing
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

### Install Packages
This installs the package manager uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
exec $SHELL
```

Now install dependencies as per pyproject.toml:
```bash
uv sync
```

### Generate Protobufs
The SDK uses protobuf definitions to generate gRPC and model classes.

Run:
```bash
uv run python generate_proto.py
```

