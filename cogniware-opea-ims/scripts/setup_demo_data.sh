#!/bin/bash
################################################################################
# Cogniware Core - Setup Demo Data
# Creates demo organization, license, and configures existing users
################################################################################

API_BASE="http://localhost:8099"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          COGNIWARE CORE - SETUP DEMO DATA                        ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Login as super admin
echo "1. Logging in as super admin..."
TOKEN=$(curl -s -X POST $API_BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' \
  | jq -r '.token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Failed to login. Make sure admin server is running on port 8099"
    exit 1
fi

echo "✅ Logged in successfully"
echo ""

# Get existing Cogniware org
echo "2. Getting Cogniware organization..."
ORGS=$(curl -s $API_BASE/admin/organizations \
  -H "Authorization: Bearer $TOKEN")

COGNIWARE_ORG=$(echo $ORGS | jq -r '.organizations[] | select(.org_name == "Cogniware Incorporated") | .org_id')

if [ -z "$COGNIWARE_ORG" ] || [ "$COGNIWARE_ORG" = "null" ]; then
    echo "❌ Cogniware organization not found"
    exit 1
fi

echo "✅ Found organization: $COGNIWARE_ORG"
echo ""

# Create enterprise license for Cogniware org
echo "3. Creating enterprise license for Cogniware..."
LICENSE_RESULT=$(curl -s -X POST $API_BASE/admin/licenses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"org_id\": \"$COGNIWARE_ORG\",
    \"license_type\": \"enterprise\",
    \"features\": [
      \"database\",
      \"code_generation\",
      \"documents\",
      \"integration\",
      \"workflow\",
      \"browser_automation\",
      \"rpa\"
    ],
    \"max_users\": 100,
    \"max_api_calls\": 10000000,
    \"days_valid\": 3650
  }")

LICENSE_KEY=$(echo $LICENSE_RESULT | jq -r '.license_key')

if [ -z "$LICENSE_KEY" ] || [ "$LICENSE_KEY" = "null" ]; then
    echo "⚠️  License may already exist, checking..."
    
    # Check existing licenses
    EXISTING=$(curl -s "$API_BASE/admin/licenses?org_id=$COGNIWARE_ORG" \
      -H "Authorization: Bearer $TOKEN")
    
    LICENSE_KEY=$(echo $EXISTING | jq -r '.licenses[0].license_key')
    
    if [ ! -z "$LICENSE_KEY" ] && [ "$LICENSE_KEY" != "null" ]; then
        echo "✅ Found existing license: $LICENSE_KEY"
    else
        echo "❌ Failed to create or find license"
        exit 1
    fi
else
    echo "✅ License created: $LICENSE_KEY"
fi

echo ""

# Create demo customer organization
echo "4. Creating demo customer organization..."
DEMO_ORG_RESULT=$(curl -s -X POST $API_BASE/admin/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "Demo Corporation",
    "org_type": "customer",
    "contact_email": "demo@democorp.com",
    "contact_phone": "+1-555-DEMO",
    "address": "123 Demo Street, Demo City, DC 12345"
  }')

DEMO_ORG=$(echo $DEMO_ORG_RESULT | jq -r '.org_id')

if [ ! -z "$DEMO_ORG" ] && [ "$DEMO_ORG" != "null" ]; then
    echo "✅ Demo organization created: $DEMO_ORG"
else
    echo "⚠️  Demo organization may already exist"
fi

echo ""

# Create license for demo org
if [ ! -z "$DEMO_ORG" ] && [ "$DEMO_ORG" != "null" ]; then
    echo "5. Creating license for demo organization..."
    DEMO_LICENSE=$(curl -s -X POST $API_BASE/admin/licenses \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"org_id\": \"$DEMO_ORG\",
        \"license_type\": \"professional\",
        \"features\": [
          \"database\",
          \"code_generation\",
          \"documents\",
          \"integration\",
          \"workflow\"
        ],
        \"max_users\": 20,
        \"max_api_calls\": 500000,
        \"days_valid\": 365
      }" | jq -r '.license_key')
    
    echo "✅ Demo license created: $DEMO_LICENSE"
    echo ""
fi

# Create demo user
if [ ! -z "$DEMO_ORG" ] && [ "$DEMO_ORG" != "null" ]; then
    echo "6. Creating demo user..."
    DEMO_USER=$(curl -s -X POST $API_BASE/admin/users \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"org_id\": \"$DEMO_ORG\",
        \"username\": \"demouser\",
        \"email\": \"demo@democorp.com\",
        \"password\": \"Demo123!\",
        \"full_name\": \"Demo User\",
        \"role\": \"user\"
      }")
    
    echo "✅ Demo user created: demouser / Demo123!"
    echo ""
fi

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              DEMO DATA SETUP COMPLETE!                           ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  ✅ Cogniware Org: $COGNIWARE_ORG"
echo "  ✅ Cogniware License: $LICENSE_KEY"
echo "  ✅ Demo Org: ${DEMO_ORG:-'(not created)'}"
echo "  ✅ Demo License: ${DEMO_LICENSE:-'(not created)'}"
echo ""
echo "Login Credentials:"
echo "  Super Admin: superadmin / Cogniware@2025"
echo "  Your Account: deadbrainviv / (your password)"
echo "  Demo User: demouser / Demo123!"
echo ""
echo "Your account (deadbrainviv) now has a full enterprise license!"
echo "You can use all features in the user portal."
echo ""
echo "Open the portal and try again!"
echo ""

