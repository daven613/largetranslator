import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
env_path = backend_dir / ".env"
test_env_path = backend_dir / "test_end_to_end" / ".test_env"

print(f"Loading main .env from: {env_path}")
loaded_main = load_dotenv(env_path)
print(f"Main .env loaded: {loaded_main}")

if test_env_path.exists():
    print(f"Loading test .env from: {test_env_path}")
    loaded_test = load_dotenv(test_env_path, override=True)
    print(f"Test .env loaded and overridding: {loaded_test}")
else:
    print(f"Test .env not found at: {test_env_path}")

print("--- Environment Variables Seen by Python ---")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_ANON_PUBLIC: {os.getenv('SUPABASE_ANON_PUBLIC')}")
print(f"SUPABASE_SERVICE_ROLE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}")
print(f"SUPABASE_KEY (old name, for checking): {os.getenv('SUPABASE_KEY')}")
print("----------------------------------------")

if os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
    print("SUCCESS: SUPABASE_SERVICE_ROLE_KEY is accessible!")
else:
    print("FAILURE: SUPABASE_SERVICE_ROLE_KEY is NOT accessible.") 