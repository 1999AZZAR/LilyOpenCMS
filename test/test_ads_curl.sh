#!/bin/bash
# Curl commands to test ads API
# Make sure server is running on localhost:5000

BASE_URL="http://localhost:5000"
COOKIE_JAR="cookies.txt"

echo "🧪 Testing Ads API with cURL"
echo "="*40

# First login to get session
echo "📝 Step 1: Login to get session..."
curl -c $COOKIE_JAR -X POST $BASE_URL/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=suadmin&password=suladang" \
  -s -o /dev/null -w "Login Status: %{http_code}\n"

if [ $? -eq 0 ]; then
    echo "✅ Login successful"
else
    echo "❌ Login failed"
    exit 1
fi

echo ""
echo "📡 Step 2: Test ad serving API..."
echo "Request: POST $BASE_URL/ads/api/serve"
echo "Data: {'page_type': 'home', 'section': 'sidebar', 'position': 'top'}"

RESPONSE=$(curl -b $COOKIE_JAR -X POST $BASE_URL/ads/api/serve \
  -H "Content-Type: application/json" \
  -d '{"page_type": "home", "section": "sidebar", "position": "top", "max_ads": 1}' \
  -s)

echo "Response Status: $?"
echo "Response Body:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

echo ""
echo "📊 Step 3: Test analytics API..."
echo "Request: GET $BASE_URL/ads/api/analytics/stats"

RESPONSE=$(curl -b $COOKIE_JAR -X GET $BASE_URL/ads/api/analytics/stats \
  -H "Content-Type: application/json" \
  -s)

echo "Response Status: $?"
echo "Response Body:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

echo ""
echo "🎯 Step 4: Test batch ad serving..."
echo "Request: POST $BASE_URL/ads/api/serve/batch"

BATCH_DATA='{
  "placements": [
    {"page_type": "home", "section": "sidebar", "position": "top"},
    {"page_type": "home", "section": "content", "position": "middle"}
  ]
}'

echo "Data: $BATCH_DATA"

RESPONSE=$(curl -b $COOKIE_JAR -X POST $BASE_URL/ads/api/serve/batch \
  -H "Content-Type: application/json" \
  -d "$BATCH_DATA" \
  -s)

echo "Response Status: $?"
echo "Response Body:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

echo ""
echo "📈 Step 5: Test external ads API..."
echo "Request: POST $BASE_URL/ads/api/external/serve"

EXTERNAL_DATA='{
  "page_type": "home",
  "section": "banner",
  "position": "top",
  "device_type": "desktop",
  "max_ads": 1
}'

echo "Data: $EXTERNAL_DATA"

RESPONSE=$(curl -X POST $BASE_URL/ads/api/external/serve \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d "$EXTERNAL_DATA" \
  -s)

echo "Response Status: $?"
echo "Response Body:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

echo ""
echo "🧹 Cleanup..."
rm -f $COOKIE_JAR

echo ""
echo "✅ Testing completed!"
echo ""
echo "📋 Summary of endpoints tested:"
echo "- POST /ads/api/serve (internal ads)"
echo "- GET /ads/api/analytics/stats (analytics)"
echo "- POST /ads/api/serve/batch (batch serving)"
echo "- POST /ads/api/external/serve (external ads)"
echo ""
echo "🌐 Dashboard URLs:"
echo "- http://localhost:5000/ads/dashboard"
echo "- http://localhost:5000/ads/analytics"
echo "- http://localhost:5000/ads/ads"
echo "- http://localhost:5000/ads/campaigns"
