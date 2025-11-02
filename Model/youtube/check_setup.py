"""
Quick setup checker for YouTube API integration
Run this to verify your GCP setup is correct
"""

import os
import sys

def check_setup():
    """Check if YouTube API setup is complete."""
    print("=" * 70)
    print("🔍 YouTube API Setup Checker")
    print("=" * 70)
    print()
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Client secrets file
    checks_total += 1
    print(f"[{checks_total}] Checking for client_secrets.json...")
    if os.path.exists("client_secrets.json"):
        print("   ✅ Found client_secrets.json")
        checks_passed += 1
        
        # Verify it's valid JSON
        try:
            import json
            with open("client_secrets.json", "r") as f:
                data = json.load(f)
                if "installed" in data or "web" in data:
                    print("   ✅ File format looks correct")
                else:
                    print("   ⚠️  File format may be incorrect")
        except Exception as e:
            print(f"   ⚠️  Error reading file: {e}")
    else:
        print("   ❌ client_secrets.json NOT FOUND")
        print("   📋 Download OAuth 2.0 credentials from GCP Console")
        print("   📍 Place in: D:\\Barclays\\ProjectKaarigar\\Model\\youtube\\")
    
    # Check 2: Required packages
    checks_total += 1
    print(f"\n[{checks_total}] Checking for required packages...")
    required_packages = [
        "google_auth_oauthlib",
        "google.auth",
        "googleapiclient"
    ]
    
    all_packages_found = True
    for package in required_packages:
        try:
            if package == "google_auth_oauthlib":
                import google_auth_oauthlib
            elif package == "google.auth":
                import google.auth
            elif package == "googleapiclient":
                import googleapiclient
            print(f"   ✅ {package} installed")
        except ImportError:
            print(f"   ❌ {package} NOT installed")
            all_packages_found = False
    
    if all_packages_found:
        checks_passed += 1
    else:
        print("\n   📦 Install missing packages:")
        print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    
    # Check 3: Token files (optional, but good to know)
    checks_total += 1
    print(f"\n[{checks_total}] Checking for authentication tokens...")
    token_files = ["token.pickle", "token_analytics.pickle"]
    has_any_token = False
    
    for token_file in token_files:
        if os.path.exists(token_file):
            print(f"   ✅ Found {token_file} (already authenticated)")
            has_any_token = True
        else:
            print(f"   ℹ️  {token_file} not found (will be created on first run)")
    
    if has_any_token:
        checks_passed += 1
    else:
        print("   ℹ️  You'll need to authenticate when running scripts")
        checks_passed += 1  # Not an error, just informational
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Setup Status: {checks_passed}/{checks_total} checks passed")
    print("=" * 70)
    
    if checks_passed == checks_total:
        print("\n🎉 All checks passed! You're ready to go!")
        print("\n📋 Next steps:")
        print("   1. Run: python yt_analytics.py   (to view channel analytics)")
        print("   2. Run: python yt_short.py        (to upload a video)")
        print("\n⚠️  First run will open browser for authentication")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\n📖 See YOUTUBE_SETUP_GUIDE.md for detailed instructions")
    
    print()
    return checks_passed == checks_total

def check_gcp_apis():
    """Attempt to verify GCP APIs are enabled (requires auth)."""
    print("\n" + "=" * 70)
    print("🌐 GCP API Status Check")
    print("=" * 70)
    print()
    print("ℹ️  To verify APIs are enabled in GCP:")
    print("   1. Go to: https://console.cloud.google.com/")
    print("   2. Select project: karigar-475215")
    print("   3. Go to: APIs & Services → Dashboard")
    print("   4. Verify these APIs are enabled:")
    print("      • YouTube Data API v3")
    print("      • YouTube Analytics API")
    print()
    
    confirm = input("Have you enabled both APIs? (y/n): ").strip().lower()
    if confirm == 'y':
        print("   ✅ Great! APIs are enabled")
        return True
    else:
        print("   ⚠️  Please enable the APIs before proceeding")
        print("   📖 See YOUTUBE_SETUP_GUIDE.md Step 1 for instructions")
        return False

if __name__ == "__main__":
    print("\n🚀 YouTube API Setup Checker for Karigar Project\n")
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📂 Working directory: {os.getcwd()}\n")
    
    # Run checks
    setup_ok = check_setup()
    
    if setup_ok:
        apis_ok = check_gcp_apis()
        
        if apis_ok:
            print("\n✅ Setup is complete!")
            print("\n🎬 Ready to test? Run:")
            print("   python yt_analytics.py")
        else:
            print("\n⚠️  Please enable APIs in GCP Console")
    
    print()
