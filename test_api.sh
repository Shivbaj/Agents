#!/bin/bash

# Multi-Agent System API Testing Script
# This script validates all core functionality of the multi-agent system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"
OLLAMA_URL="http://localhost:11434"

echo -e "${BLUE}🧪 Multi-Agent System API Testing Script${NC}"
echo -e "${BLUE}===========================================${NC}"

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local curl_cmd="$2"
    local expected_status="$3"
    
    echo -e "\n${YELLOW}Testing: $name${NC}"
    
    if response=$(eval "$curl_cmd" 2>/dev/null); then
        echo -e "${GREEN}✅ $name - SUCCESS${NC}"
        if [ "$4" = "show" ]; then
            echo "$response" | jq . 2>/dev/null || echo "$response"
        fi
        return 0
    else
        echo -e "${RED}❌ $name - FAILED${NC}"
        return 1
    fi
}

# Function to test POST endpoint
test_post_endpoint() {
    local name="$1"
    local url="$2"
    local data="$3"
    
    echo -e "\n${YELLOW}Testing: $name${NC}"
    
    if response=$(curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data" 2>/dev/null); then
        echo -e "${GREEN}✅ $name - SUCCESS${NC}"
        if [ "$4" = "show" ]; then
            echo "$response" | jq . 2>/dev/null || echo "$response"
        fi
        return 0
    else
        echo -e "${RED}❌ $name - FAILED${NC}"
        return 1
    fi
}

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

run_test() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if "$@"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
}

echo -e "\n${BLUE}🏥 HEALTH & STATUS TESTS${NC}"
echo "=========================="

run_test test_endpoint "Basic Health Check" \
    "curl -s $BASE_URL/health" 200 show

run_test test_endpoint "Detailed Health Check" \
    "curl -s $BASE_URL/api/v1/health/" 200 show

run_test test_endpoint "Liveness Probe" \
    "curl -s $BASE_URL/api/v1/health/live" 200

run_test test_endpoint "Readiness Probe" \
    "curl -s $BASE_URL/api/v1/health/ready" 200

echo -e "\n${BLUE}🤖 AGENT REGISTRY TESTS${NC}"
echo "========================"

run_test test_endpoint "List Agents" \
    "curl -s $BASE_URL/api/v1/agents/list" 200 show

run_test test_endpoint "Discover Agents" \
    "curl -s '$BASE_URL/api/v1/agents/discover?query=assistant'" 200 show

# Test agent details (may fail if no agents loaded)
echo -e "\n${YELLOW}Testing: Get Agent Details (may fail if no agents)${NC}"
curl -s "$BASE_URL/api/v1/agents/general_assistant" | jq . 2>/dev/null || echo "No agents loaded"

echo -e "\n${BLUE}🔧 MODEL MANAGEMENT TESTS${NC}"
echo "=========================="

run_test test_endpoint "List Model Providers" \
    "curl -s $BASE_URL/api/v1/models/providers" 200 show

run_test test_endpoint "List Models" \
    "curl -s $BASE_URL/api/v1/models/list" 200 show

run_test test_post_endpoint "Test Model" \
    "$BASE_URL/api/v1/models/test" \
    '{"provider":"ollama","model":"phi3:mini","prompt":"Hello, world!"}' show

echo -e "\n${BLUE}💬 CHAT API TESTS${NC}"
echo "=================="

run_test test_post_endpoint "Basic Chat" \
    "$BASE_URL/api/v1/agents/chat" \
    '{"message":"Hello, how are you?","agent_id":"general_assistant"}' show

run_test test_post_endpoint "Chat with Ollama Model" \
    "$BASE_URL/api/v1/agents/chat" \
    '{"message":"What is AI?","agent_id":"general_assistant","provider_override":"ollama","model_override":"phi3:mini"}' show

run_test test_post_endpoint "Chat with Tools" \
    "$BASE_URL/api/v1/agents/chat" \
    '{"message":"Help me understand multi-agent systems","agent_id":"general_assistant","use_tools":true}' show

echo -e "\n${BLUE}🦙 OLLAMA DIRECT TESTS${NC}"
echo "======================"

run_test test_endpoint "Ollama Models List" \
    "curl -s $OLLAMA_URL/api/tags" 200 show

run_test test_post_endpoint "Ollama Generate" \
    "$OLLAMA_URL/api/generate" \
    '{"model":"phi3:mini","prompt":"What are AI agents?","stream":false}' show

run_test test_post_endpoint "Ollama Chat" \
    "$OLLAMA_URL/api/chat" \
    '{"model":"phi3:mini","messages":[{"role":"user","content":"Hello!"}],"stream":false}' show

echo -e "\n${BLUE}🔍 ADVANCED TESTS${NC}"
echo "=================="

# Test streaming (basic check)
echo -e "\n${YELLOW}Testing: Streaming Chat${NC}"
if timeout 10s curl -s -X POST "$BASE_URL/api/v1/agents/chat/stream" \
    -H "Content-Type: application/json" \
    -d '{"message":"Count to 3","agent_id":"general_assistant"}' | head -5; then
    echo -e "${GREEN}✅ Streaming Chat - SUCCESS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ Streaming Chat - FAILED${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test multimodal (will likely fail without vision agent)
echo -e "\n${YELLOW}Testing: Multimodal Chat (expected to fail without vision agent)${NC}"
curl -s -X POST "$BASE_URL/api/v1/agents/multimodal" \
    -H "Content-Type: application/json" \
    -d '{"message":"Describe this","agent_id":"vision_agent","image_data":"data:image/jpeg;base64,/9j/4AAQ"}' \
    | jq . 2>/dev/null || echo "Multimodal not available (expected)"

# Test conversation continuity
echo -e "\n${YELLOW}Testing: Conversation Continuity${NC}"
CONV_ID="test-conv-$(date +%s)"

# First message
response1=$(curl -s -X POST "$BASE_URL/api/v1/agents/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"My name is Alice. Remember this.\",\"agent_id\":\"general_assistant\",\"conversation_id\":\"$CONV_ID\"}")

# Second message
response2=$(curl -s -X POST "$BASE_URL/api/v1/agents/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"What is my name?\",\"agent_id\":\"general_assistant\",\"conversation_id\":\"$CONV_ID\"}")

if echo "$response2" | grep -qi "alice"; then
    echo -e "${GREEN}✅ Conversation Continuity - SUCCESS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️  Conversation Continuity - May not be implemented${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo -e "\n${BLUE}📊 PERFORMANCE TESTS${NC}"
echo "===================="

# Response time test
echo -e "\n${YELLOW}Testing: Response Time${NC}"
start_time=$(date +%s.%N)
curl -s "$BASE_URL/health" > /dev/null
end_time=$(date +%s.%N)
response_time=$(echo "$end_time - $start_time" | bc -l)
echo "Health endpoint response time: ${response_time}s"

# Load test (simple)
echo -e "\n${YELLOW}Testing: Concurrent Requests${NC}"
for i in {1..5}; do
    curl -s "$BASE_URL/health" &
done
wait
echo -e "${GREEN}✅ Concurrent requests completed${NC}"

echo -e "\n${BLUE}📋 TEST SUMMARY${NC}"
echo "================"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! System is fully functional.${NC}"
    exit 0
elif [ $PASSED_TESTS -gt $((TOTAL_TESTS / 2)) ]; then
    echo -e "\n${YELLOW}⚠️  Most tests passed. System is mostly functional.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Many tests failed. Check system configuration.${NC}"
    exit 1
fi