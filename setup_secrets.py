"""
setup_secrets.py — Reads your .env file and pushes all 4 secrets to GitHub Actions.

Run once:  python setup_secrets.py

You will be asked for a GitHub Personal Access Token.
How to create one (takes 1 minute):
  1. Go to: https://github.com/settings/tokens/new
  2. Give it any name (e.g. "AI News Digest setup")
  3. Set expiration: 7 days (you only need it once)
  4. Tick ONE box: repo -> (full repo access)
  5. Click "Generate token" and copy it
"""

import base64
import os
import sys
import json

try:
    from dotenv import dotenv_values
    import urllib.request
except ImportError:
    print("Run:  pip install python-dotenv  first.")
    sys.exit(1)

REPO = "hovavalster/AI_News_Digest"
SECRET_NAMES = ["ANTHROPIC_API_KEY", "EMAIL_SENDER", "EMAIL_PASSWORD", "EMAIL_RECIPIENT"]

def get_public_key(token: str) -> tuple[str, str]:
    """Fetch the repo's public key needed to encrypt secrets."""
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["key_id"], data["key"]

def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encrypt a secret value using the repo's public key (libsodium / nacl)."""
    try:
        from nacl import encoding, public as nacl_public
    except ImportError:
        print("\nInstalling PyNaCl (needed to encrypt secrets)...")
        os.system(f"{sys.executable} -m pip install PyNaCl --quiet")
        from nacl import encoding, public as nacl_public

    public_key = nacl_public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder)
    sealed_box = nacl_public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()

def set_secret(token: str, key_id: str, key_b64: str, name: str, value: str) -> bool:
    """Upload one encrypted secret to GitHub."""
    encrypted = encrypt_secret(key_b64, value)
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/{name}"
    body = json.dumps({"encrypted_value": encrypted, "key_id": key_id}).encode()
    req = urllib.request.Request(url, data=body, method="PUT", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status in (201, 204)
    except Exception as e:
        print(f"  ERROR setting {name}: {e}")
        return False

def main():
    print("=" * 55)
    print("  GitHub Secrets Setup for AI News Digest")
    print("=" * 55)

    # Load .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        print("ERROR: .env file not found. Create it first.")
        sys.exit(1)

    env = dotenv_values(env_path)
    missing = [k for k in SECRET_NAMES if not env.get(k)]
    if missing:
        print(f"ERROR: Missing values in .env: {', '.join(missing)}")
        sys.exit(1)

    # Get token
    print("\nStep 1: Create a GitHub token at:")
    print("  https://github.com/settings/tokens/new")
    print("  -> Tick: repo (full access)")
    print("  -> Expiration: 7 days is fine\n")
    token = input("Paste your GitHub token here: ").strip()
    if not token:
        print("No token entered. Exiting.")
        sys.exit(1)

    # Fetch public key
    print("\nConnecting to GitHub...")
    try:
        key_id, key_b64 = get_public_key(token)
    except Exception as e:
        print(f"ERROR: Could not connect to GitHub: {e}")
        print("Check your token has 'repo' access.")
        sys.exit(1)

    # Upload secrets
    print(f"\nUploading {len(SECRET_NAMES)} secrets to {REPO}...")
    all_ok = True
    for name in SECRET_NAMES:
        value = env[name]
        ok = set_secret(token, key_id, key_b64, name, value)
        status = "OK" if ok else "FAILED"
        print(f"  {status}  {name}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("All secrets uploaded successfully!")
        print(f"\nYour GitHub Actions workflow is ready:")
        print(f"  https://github.com/{REPO}/actions")
        print("\nTo trigger it manually: Actions tab -> 'Daily AI News Digest' -> 'Run workflow'")
    else:
        print("Some secrets failed. Check the errors above.")

if __name__ == "__main__":
    main()
