import os
from dotenv import load_dotenv

load_dotenv()  # loads .env

operator_id = os.getenv("OPERATOR_ID")
operator_key = os.getenv("OPERATOR_KEY")
network = os.getenv("NETWORK")

print("OPERATOR_ID:", operator_id)
print("OPERATOR_KEY:", operator_key[:10] + "..." if operator_key else None)
print("NETWORK:", network)

if not operator_id or not operator_key or not network:
    print("❌ One or more environment variables are missing or incorrect")
else:
    print("✅ All environment variables are set correctly")
