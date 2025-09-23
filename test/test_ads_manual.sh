#!/bin/bash
# Manual test script for ads system
# Run this after starting the server: python main.py

echo "🧪 Manual Ads System Test"
echo "="*40

BASE_URL="http://localhost:5000"

echo "📝 Testing Login..."
echo "Use credentials: suadmin / suladang"
echo "Login URL: $BASE_URL/login"

echo ""
echo "📡 Test API Endpoints:"
echo ""

echo "1️⃣  Test Ad Serving API:"
echo "curl -X POST $BASE_URL/ads/api/serve \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"page_type\": \"home\", \"section\": \"sidebar\", \"position\": \"top\", \"max_ads\": 1}'"
echo ""

echo "2️⃣  Test Batch Ad Serving:"
echo "curl -X POST $BASE_URL/ads/api/serve/batch \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"placements\": [{\"page_type\": \"home\", \"section\": \"sidebar\", \"position\": \"top\"}]}'"
echo ""

echo "3️⃣  Test External Ads API:"
echo "curl -X POST $BASE_URL/ads/api/external/serve \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'X-API-Key: your-api-key' \\"
echo "  -d '{\"page_type\": \"home\", \"section\": \"banner\", \"position\": \"top\"}'"
echo ""

echo "4️⃣  Test Impression Tracking:"
echo "curl -X POST $BASE_URL/ads/api/track-impression \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"ad_id\": 1, \"placement_id\": 1, \"user_id\": null}'"
echo ""

echo "5️⃣  Test Click Tracking:"
echo "curl -X POST $BASE_URL/ads/api/track-click \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"ad_id\": 1, \"placement_id\": 1, \"user_id\": null, \"click_url\": \"https://example.com\"}'"
echo ""

echo "📊 Dashboard URLs:"
echo "- Main Dashboard: $BASE_URL/ads/dashboard"
echo "- Campaigns: $BASE_URL/ads/campaigns"
echo "- Ads Management: $BASE_URL/ads/ads"
echo "- Placements: $BASE_URL/ads/placements"
echo "- Analytics: $BASE_URL/ads/analytics"
echo "- Image Management: $BASE_URL/ads/images"
echo ""

echo "🔧 To run the full test script:"
echo "cd /home/azzar/project/LOC/LILYOPENCMS"
echo "python test_push_ad.py"
echo ""

echo "✅ Make sure the server is running on port 5000 first!"
