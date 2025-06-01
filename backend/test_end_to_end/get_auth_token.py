import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

def update_jwt_in_env_file(env_file_path: Path, jwt_token: str):
    """Updates the SUPABASE_TEST_JWT in the specified .env file."""
    lines = []
    found = False
    if env_file_path.exists():
        with open(env_file_path, 'r') as f:
            lines = f.readlines()

    with open(env_file_path, 'w') as f:
        for line in lines:
            if line.startswith('SUPABASE_TEST_JWT='):
                f.write(f'SUPABASE_TEST_JWT={jwt_token}\n')
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f'SUPABASE_TEST_JWT={jwt_token}\n')
    print(f"JWT token updated in {env_file_path}")

def main():
    """Fetches Supabase JWT and updates it in the .test_env file."""
    # Define paths
    # Script is in backend/test_end_to_end, so .env is two levels up in backend/
    # and .test_env is one level up in backend/test_end_to_end/
    script_dir = Path(__file__).resolve().parent
    backend_env_path = script_dir.parent / '.env'
    test_env_path = script_dir / '.test_env' # As per user's setup

    # Load credentials from backend/.env
    if not backend_env_path.exists():
        print(f"Error: {backend_env_path} not found.")
        print("Please ensure your backend/.env file exists and contains SUPABASE_URL and SUPABASE_KEY.")
        return
    load_dotenv(dotenv_path=backend_env_path)

    # Load test user credentials from .test_env (in the same directory as this script)
    if not test_env_path.exists():
        print(f"Error: {test_env_path} not found.")
        print(f"Please ensure {test_env_path} exists and contains SUPABASE_TEST_USER_EMAIL and SUPABASE_TEST_USER_PASSWORD.")
        return
    load_dotenv(dotenv_path=test_env_path, override=True) # Override to ensure we get .test_env vars if names overlap

    supabase_url = os.getenv('SUPABASE_URL')
    # User specified SUPABASE_KEY instead of SUPABASE_ANON_KEY
    supabase_key = os.getenv('SUPABASE_KEY') 
    test_user_email = os.getenv('SUPABASE_TEST_USER_EMAIL')
    test_user_password = os.getenv('SUPABASE_TEST_USER_PASSWORD')

    if not all([supabase_url, supabase_key, test_user_email, test_user_password]):
        print("Error: Missing one or more required environment variables.")
        print(f"  SUPABASE_URL: {'Found' if supabase_url else 'Missing from backend/.env'}")
        print(f"  SUPABASE_KEY: {'Found' if supabase_key else 'Missing from backend/.env'}")
        print(f"  SUPABASE_TEST_USER_EMAIL: {'Found' if test_user_email else f'Missing from {test_env_path}'}")
        print(f"  SUPABASE_TEST_USER_PASSWORD: {'Found' if test_user_password else f'Missing from {test_env_path}'}")
        return

    try:
        print(f"Attempting to sign in as {test_user_email}...")
        supabase: Client = create_client(supabase_url, supabase_key)
        response = supabase.auth.sign_in_with_password(
            {"email": test_user_email, "password": test_user_password}
        )
        
        jwt_token = response.session.access_token
        print("Successfully obtained JWT token.")
        
        update_jwt_in_env_file(test_env_path, jwt_token)
        
    except Exception as e:
        print(f"Error obtaining JWT token: {e}")
        if hasattr(e, 'details'):
            print(f"Details: {e.details}")
        if hasattr(e, 'message'): # SupabaseHTTPException often has a message
             print(f"Message: {e.message}")

if __name__ == "__main__":
    main()
