#!/usr/bin/env python3
"""
Environment setup validation script for Hiero SDK Python examples.

This script validates your .env file and testnet credentials to ensure
they are properly configured for running examples.

Usage:
    python docs/setup_env.py

The script should be run from the project root directory.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add the src directory to the path so we can import the SDK
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from hiero_sdk_python import PrivateKey, AccountId, Client
    from hiero_sdk_python.client import Network
except ImportError as e:
    print(f"❌ Error importing SDK: {e}")
    print("Make sure you have installed the SDK dependencies:")
    print("  uv sync")
    print("  # or")
    print("  pip install -e .")
    sys.exit(1)


def validate_private_key(private_key: str) -> bool:
    """
    Validate a private key using the SDK's PrivateKey.from_string method.
    This handles various key formats including DER and hex strings.
    """
    try:
        PrivateKey.from_string(private_key)
        return True
    except Exception:
        return False


def validate_account_id(account_id: str) -> bool:
    """
    Validate an account ID format.
    """
    try:
        AccountId.from_string(account_id)
        return True
    except Exception:
        return False


def check_env_file() -> Optional[dict]:
    """
    Check if .env file exists and load its contents.
    """
    env_path = project_root / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found in project root")
        print("Create a .env file with your testnet credentials:")
        print("  OPERATOR_ID=0.0.1234xx")
        print("  OPERATOR_KEY=your_private_key_here")
        print("  NETWORK=testnet")
        return None
    
    print("✅ .env file found")
    
    # Load environment variables
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def validate_required_vars(env_vars: dict) -> bool:
    """
    Validate required environment variables.
    """
    required_vars = ['OPERATOR_ID', 'OPERATOR_KEY', 'NETWORK']
    missing_vars = []
    
    for var in required_vars:
        if var not in env_vars:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables present")
    return True


def validate_credentials(env_vars: dict) -> bool:
    """
    Validate the format of credentials.
    """
    all_valid = True
    
    # Validate account ID
    account_id = env_vars.get('OPERATOR_ID')
    if account_id:
        if validate_account_id(account_id):
            print(f"✅ Account ID format valid: {account_id}")
        else:
            print(f"❌ Invalid account ID format: {account_id}")
            print("  Account ID should be in format: 0.0.1234")
            all_valid = False
    
    # Validate private key
    private_key = env_vars.get('OPERATOR_KEY')
    if private_key:
        if validate_private_key(private_key):
            print("✅ Private key format valid")
        else:
            print("❌ Invalid private key format")
            print("  Private key should be a valid hex string or DER format")
            all_valid = False
    
    # Validate network
    network = env_vars.get('NETWORK')
    if network:
        if network.lower() in ['testnet', 'mainnet', 'previewnet']:
            print(f"✅ Network valid: {network}")
            if network.lower() != 'testnet':
                print("⚠️  Warning: Examples are designed for testnet. Mainnet/previewnet may not work as expected.")
        else:
            print(f"❌ Invalid network: {network}")
            print("  Network should be one of: testnet, mainnet, previewnet")
            all_valid = False
    
    return all_valid


def test_network_connection(env_vars: dict) -> bool:
    """
    Test network connectivity with the provided credentials.
    """
    try:
        operator_id = env_vars.get('OPERATOR_ID')
        operator_key = env_vars.get('OPERATOR_KEY')
        network = env_vars.get('NETWORK', 'testnet')
        
        if not all([operator_id, operator_key]):
            print("❌ Cannot test connection: missing credentials")
            return False
        
        print(f"🔄 Testing connection to {network}...")
        
        # Create client
        client = Client.for_network(Network.from_string(network))
        client.set_operator(AccountId.from_string(operator_id), PrivateKey.from_string(operator_key))
        
        # Test with a simple balance query
        from hiero_sdk_python import CryptoGetAccountBalanceQuery
        balance = CryptoGetAccountBalanceQuery(account_id=AccountId.from_string(operator_id)).execute(client)
        
        print(f"✅ Network connection successful")
        print(f"   Account balance: {balance.hbars} HBAR")
        return True
        
    except Exception as e:
        print(f"❌ Network connection failed: {e}")
        print("   Check your credentials and network connectivity")
        return False


def main():
    """
    Main validation function.
    """
    print("🔧 Hiero SDK Python - Environment Setup Validation")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not (project_root / "pyproject.toml").exists():
        print("❌ Not in project root directory")
        print("   Please run this script from the project root")
        sys.exit(1)
    
    print(f"✅ Running from project root: {project_root}")
    print()
    
    # Check .env file
    env_vars = check_env_file()
    if not env_vars:
        sys.exit(1)
    
    print()
    
    # Validate required variables
    if not validate_required_vars(env_vars):
        sys.exit(1)
    
    print()
    
    # Validate credentials
    if not validate_credentials(env_vars):
        sys.exit(1)
    
    print()
    
    # Test network connection
    if not test_network_connection(env_vars):
        sys.exit(1)
    
    print()
    print("🎉 Environment setup validation completed successfully!")
    print("   You can now run the examples:")
    print("   python examples/account_create.py")
    print("   python examples/query_balance.py")


if __name__ == "__main__":
    main()
