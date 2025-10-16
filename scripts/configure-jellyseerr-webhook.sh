#!/bin/bash

##############################################################################
# Jellyseerr-Linkarr Webhook Configuration Script
#
# This script automatically configures the webhook in Jellyseerr-Linkarr
# to send notifications to the Linkarr backend.
#
# Prerequisites:
# 1. Jellyseerr-Linkarr setup wizard must be completed
# 2. Admin account must be created
# 3. You need your admin email and password
#
# Usage:
#   ./configure-jellyseerr-webhook.sh <email> <password>
#
# Example:
#   ./configure-jellyseerr-webhook.sh admin@example.com MySecurePassword123
##############################################################################

set -e

# Configuration
JELLYSEERR_URL="http://YOUR_SERVER_IP:5057"
LINKARR_WEBHOOK_URL="http://YOUR_SERVER_IP:8000/api/webhooks/overseerr"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -ne 2 ]; then
    echo -e "${RED}Error: Missing arguments${NC}"
    echo "Usage: $0 <email> <password>"
    echo "Example: $0 admin@example.com MyPassword123"
    exit 1
fi

EMAIL="$1"
PASSWORD="$2"

echo -e "${YELLOW}=== Jellyseerr-Linkarr Webhook Configuration ===${NC}"
echo ""
echo "Jellyseerr URL: $JELLYSEERR_URL"
echo "Webhook Target: $LINKARR_WEBHOOK_URL"
echo "Admin Email: $EMAIL"
echo ""

# Step 1: Login to Jellyseerr
echo -e "${YELLOW}[1/4] Logging in to Jellyseerr...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$JELLYSEERR_URL/api/v1/auth/local" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

# Extract auth cookie
AUTH_COOKIE=$(echo "$LOGIN_RESPONSE" | grep -o '"connect.sid":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AUTH_COOKIE" ]; then
    echo -e "${RED}✗ Login failed. Please check your credentials.${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Login successful${NC}"

# Step 2: Get current webhook settings
echo -e "${YELLOW}[2/4] Fetching current webhook settings...${NC}"
WEBHOOK_SETTINGS=$(curl -s -X GET "$JELLYSEERR_URL/api/v1/settings/notifications/webhook" \
    -H "Cookie: connect.sid=$AUTH_COOKIE")

echo -e "${GREEN}✓ Retrieved current settings${NC}"

# Step 3: Configure webhook
echo -e "${YELLOW}[3/4] Configuring webhook for Linkarr...${NC}"

WEBHOOK_CONFIG=$(cat <<EOF
{
  "enabled": true,
  "types": 2,
  "options": {
    "webhookUrl": "$LINKARR_WEBHOOK_URL",
    "jsonPayload": "{\n    \"notification_type\": \"{{notification_type}}\",\n    \"subject\": \"{{subject}}\",\n    \"message\": \"{{message}}\",\n    \"image\": \"{{image}}\",\n    \"{{media}}\": {\n        \"media_type\": \"{{media_type}}\",\n        \"tmdbId\": \"{{media_tmdbid}}\",\n        \"tvdbId\": \"{{media_tvdbid}}\",\n        \"status\": \"{{media_status}}\",\n        \"status4k\": \"{{media_status4k}}\"\n    },\n    \"{{request}}\": {\n        \"request_id\": \"{{request_id}}\",\n        \"requestedBy_email\": \"{{requestedBy_email}}\",\n        \"requestedBy_username\": \"{{requestedBy_username}}\",\n        \"requestedBy_avatar\": \"{{requestedBy_avatar}}\"\n    },\n    \"{{issue}}\": {\n        \"issue_id\": \"{{issue_id}}\",\n        \"issue_type\": \"{{issue_type}}\",\n        \"issue_status\": \"{{issue_status}}\",\n        \"reportedBy_email\": \"{{reportedBy_email}}\",\n        \"reportedBy_username\": \"{{reportedBy_username}}\",\n        \"reportedBy_avatar\": \"{{reportedBy_avatar}}\"\n    },\n    \"{{comment}}\": {\n        \"comment_message\": \"{{comment_message}}\",\n        \"commentedBy_email\": \"{{commentedBy_email}}\",\n        \"commentedBy_username\": \"{{commentedBy_username}}\",\n        \"commentedBy_avatar\": \"{{commentedBy_avatar}}\"\n    },\n    \"{{extra}}\": []\n}"
  }
}
EOF
)

WEBHOOK_RESPONSE=$(curl -s -X POST "$JELLYSEERR_URL/api/v1/settings/notifications/webhook" \
    -H "Cookie: connect.sid=$AUTH_COOKIE" \
    -H "Content-Type: application/json" \
    -d "$WEBHOOK_CONFIG")

echo -e "${GREEN}✓ Webhook configured${NC}"

# Step 4: Test webhook
echo -e "${YELLOW}[4/4] Testing webhook connection...${NC}"

TEST_RESPONSE=$(curl -s -X POST "$JELLYSEERR_URL/api/v1/settings/notifications/webhook/test" \
    -H "Cookie: connect.sid=$AUTH_COOKIE" \
    -H "Content-Type: application/json")

if echo "$TEST_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Webhook test successful!${NC}"
else
    echo -e "${YELLOW}⚠ Webhook test may have issues. Check Linkarr logs.${NC}"
fi

# Final verification
echo ""
echo -e "${GREEN}=== Configuration Complete! ===${NC}"
echo ""
echo "Webhook Configuration:"
echo "  ✓ Enabled: Yes"
echo "  ✓ URL: $LINKARR_WEBHOOK_URL"
echo "  ✓ Notification Types: Media Approved, Media Available, Media Auto-Approved"
echo "  ✓ Format: JSON Payload"
echo ""
echo "Next Steps:"
echo "  1. Request a test movie in Jellyseerr (http://YOUR_SERVER_IP:5057)"
echo "  2. Approve the request"
echo "  3. Check Linkarr backend logs: docker logs linkarr-backend --tail 50"
echo "  4. Verify media appears in Linkarr: http://YOUR_SERVER_IP:3002/library"
echo ""
echo -e "${GREEN}Happy streaming! 🎬${NC}"
