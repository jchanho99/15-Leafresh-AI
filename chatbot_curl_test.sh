curl -X POST http://localhost:9000/ai/chatbot/recommendation/base-info \
  -H "Content-Type: application/json" \
  -d '{
    "location": "도시",
    "workType": "사무직",
    "category": "비건"
  }'


curl -X POST http://localhost:9000/ai/chatbot/recommendation/free-text \
  -H "Content-Type: application/json" \
  -d '{
    "message": "비건 관련 챌린지 추천"
  }'