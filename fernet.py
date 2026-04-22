# Install library: pip install cryptography
from cryptography.fernet import Fernet

# Generate a new key
key = Fernet.generate_key()

# Print key to save it (e.g., to a file or environment variable)
print(key.decode())
