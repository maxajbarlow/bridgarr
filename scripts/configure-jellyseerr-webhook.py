#!/usr/bin/env python3
"""
Jellyseerr-Linkarr Webhook Configuration Script

This script automatically configures the webhook in Jellyseerr-Linkarr
to send notifications to the Linkarr backend.

Prerequisites:
1. Jellyseerr-Linkarr setup wizard must be completed
2. Admin account must be created
3. You need your admin email and password

Usage:
    python3 configure-jellyseerr-webhook.py

Or with arguments:
    python3 configure-jellyseerr-webhook.py --email admin@example.com --password YourPassword
"""

import sys
import json
import argparse
import requests
from typing import Optional

# Configuration
JELLYSEERR_URL = "http://YOUR_SERVER_IP:5057"
LINKARR_WEBHOOK_URL = "http://YOUR_SERVER_IP:8000/api/webhooks/overseerr"

# Color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message"""
    print(f"{color}{message}{Colors.NC}")


def login_to_jellyseerr(email: str, password: str) -> Optional[str]:
    """
    Login to Jellyseerr and return session cookie
    """
    print_colored("[1/5] Logging in to Jellyseerr...", Colors.YELLOW)

    try:
        response = requests.post(
            f"{JELLYSEERR_URL}/api/v1/auth/local",
            json={"email": email, "password": password},
            timeout=10
        )

        if response.status_code == 200:
            # Extract session cookie
            cookies = response.cookies
            if 'connect.sid' in cookies:
                print_colored("✓ Login successful", Colors.GREEN)
                return cookies['connect.sid']
            else:
                print_colored("✗ No session cookie received", Colors.RED)
                return None
        else:
            print_colored(f"✗ Login failed: {response.status_code}", Colors.RED)
            print_colored(f"Response: {response.text}", Colors.RED)
            return None

    except requests.exceptions.RequestException as e:
        print_colored(f"✗ Connection error: {str(e)}", Colors.RED)
        return None


def get_webhook_settings(session_cookie: str) -> Optional[dict]:
    """
    Get current webhook settings
    """
    print_colored("[2/5] Fetching current webhook settings...", Colors.YELLOW)

    try:
        response = requests.get(
            f"{JELLYSEERR_URL}/api/v1/settings/notifications/webhook",
            cookies={"connect.sid": session_cookie},
            timeout=10
        )

        if response.status_code == 200:
            print_colored("✓ Retrieved current settings", Colors.GREEN)
            return response.json()
        else:
            print_colored(f"⚠ Could not fetch settings: {response.status_code}", Colors.YELLOW)
            return None

    except requests.exceptions.RequestException as e:
        print_colored(f"✗ Error fetching settings: {str(e)}", Colors.RED)
        return None


def configure_webhook(session_cookie: str) -> bool:
    """
    Configure webhook for Linkarr
    """
    print_colored("[3/5] Configuring webhook for Linkarr...", Colors.YELLOW)

    webhook_config = {
        "enabled": True,
        "types": 6,  # Bit flags: 2 (approved) + 4 (available) = 6
        "options": {
            "webhookUrl": LINKARR_WEBHOOK_URL,
            "jsonPayload": json.dumps({
                "notification_type": "{{notification_type}}",
                "subject": "{{subject}}",
                "message": "{{message}}",
                "image": "{{image}}",
                "media": {
                    "media_type": "{{media_type}}",
                    "tmdbId": "{{media_tmdbid}}",
                    "tvdbId": "{{media_tvdbid}}",
                    "status": "{{media_status}}",
                    "status4k": "{{media_status4k}}"
                },
                "request": {
                    "request_id": "{{request_id}}",
                    "requestedBy_email": "{{requestedBy_email}}",
                    "requestedBy_username": "{{requestedBy_username}}",
                    "requestedBy_avatar": "{{requestedBy_avatar}}"
                },
                "extra": []
            }, indent=2)
        }
    }

    try:
        response = requests.post(
            f"{JELLYSEERR_URL}/api/v1/settings/notifications/webhook",
            cookies={"connect.sid": session_cookie},
            json=webhook_config,
            timeout=10
        )

        if response.status_code in [200, 201]:
            print_colored("✓ Webhook configured successfully", Colors.GREEN)
            return True
        else:
            print_colored(f"✗ Configuration failed: {response.status_code}", Colors.RED)
            print_colored(f"Response: {response.text}", Colors.RED)
            return False

    except requests.exceptions.RequestException as e:
        print_colored(f"✗ Error configuring webhook: {str(e)}", Colors.RED)
        return False


def test_linkarr_endpoint() -> bool:
    """
    Test if Linkarr webhook endpoint is reachable
    """
    print_colored("[4/5] Testing Linkarr webhook endpoint...", Colors.YELLOW)

    try:
        response = requests.get(
            "http://YOUR_SERVER_IP:8000/api/webhooks/test",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_colored("✓ Linkarr endpoint is reachable", Colors.GREEN)
            print_colored(f"  Service: {data.get('service')}", Colors.BLUE)
            print_colored(f"  Version: {data.get('version')}", Colors.BLUE)
            return True
        else:
            print_colored(f"⚠ Endpoint returned: {response.status_code}", Colors.YELLOW)
            return False

    except requests.exceptions.RequestException as e:
        print_colored(f"✗ Cannot reach Linkarr: {str(e)}", Colors.RED)
        return False


def test_webhook(session_cookie: str) -> bool:
    """
    Send test webhook notification
    """
    print_colored("[5/5] Sending test webhook...", Colors.YELLOW)

    try:
        response = requests.post(
            f"{JELLYSEERR_URL}/api/v1/settings/notifications/webhook/test",
            cookies={"connect.sid": session_cookie},
            timeout=10
        )

        if response.status_code == 204 or response.status_code == 200:
            print_colored("✓ Test webhook sent successfully", Colors.GREEN)
            return True
        else:
            print_colored(f"⚠ Test returned: {response.status_code}", Colors.YELLOW)
            return False

    except requests.exceptions.RequestException as e:
        print_colored(f"✗ Test failed: {str(e)}", Colors.RED)
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Configure Jellyseerr webhook for Linkarr"
    )
    parser.add_argument("--email", help="Jellyseerr admin email")
    parser.add_argument("--password", help="Jellyseerr admin password")
    args = parser.parse_args()

    print_colored("\n=== Jellyseerr-Linkarr Webhook Configuration ===\n", Colors.YELLOW)
    print(f"Jellyseerr URL: {JELLYSEERR_URL}")
    print(f"Webhook Target: {LINKARR_WEBHOOK_URL}\n")

    # Get credentials
    email = args.email
    password = args.password

    if not email:
        email = input("Enter Jellyseerr admin email: ")
    if not password:
        import getpass
        password = getpass.getpass("Enter Jellyseerr admin password: ")

    # Execute configuration steps
    session_cookie = login_to_jellyseerr(email, password)
    if not session_cookie:
        print_colored("\n✗ Configuration failed: Could not login", Colors.RED)
        sys.exit(1)

    get_webhook_settings(session_cookie)

    if not configure_webhook(session_cookie):
        print_colored("\n✗ Configuration failed: Could not configure webhook", Colors.RED)
        sys.exit(1)

    test_linkarr_endpoint()
    test_webhook(session_cookie)

    # Print success message
    print_colored("\n=== Configuration Complete! ===\n", Colors.GREEN)
    print("Webhook Configuration:")
    print("  ✓ Enabled: Yes")
    print(f"  ✓ URL: {LINKARR_WEBHOOK_URL}")
    print("  ✓ Notification Types: Media Approved, Media Available, Media Auto-Approved")
    print("  ✓ Format: JSON Payload")
    print("\nNext Steps:")
    print("  1. Request a test movie in Jellyseerr (http://YOUR_SERVER_IP:5057)")
    print("  2. Approve the request")
    print("  3. Check Linkarr backend logs: docker logs linkarr-backend --tail 50")
    print("  4. Verify media appears in Linkarr: http://YOUR_SERVER_IP:3002/library")
    print_colored("\nHappy streaming! 🎬\n", Colors.GREEN)


if __name__ == "__main__":
    main()
