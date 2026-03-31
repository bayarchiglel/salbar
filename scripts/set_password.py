#!/usr/bin/env python3
"""
Change the dashboard password.
Usage:  python scripts/set_password.py YourNewPassword

Then commit data/auth.json:
    git add data/auth.json
    git commit -m "change dashboard password"
    git push
"""
import hashlib, json, sys
from pathlib import Path

AUTH = Path(__file__).parent.parent / "data" / "auth.json"

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/set_password.py <NewPassword>")
        sys.exit(1)

    pw   = sys.argv[1]
    h    = hashlib.sha256(pw.encode()).hexdigest()
    data = json.loads(AUTH.read_text(encoding="utf-8")) if AUTH.exists() else {}
    data["_comment"]      = "To change: run `python scripts/set_password.py NewPassword` then commit data/auth.json"
    data["password_hash"] = h
    data["password_hint"] = ""   # clear hint after first change
    AUTH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅  Password updated.  Hash: {h}")
    print(f"    Now run:")
    print(f"    git add data/auth.json && git commit -m 'update password' && git push")

if __name__ == "__main__":
    main()
