# PromotionService

FastAPI service managing promotion and coupon validation.

Endpoints:
- POST /promotions/validate: Validate a promotion code for an order (MVP uses hardcoded promotions, assumes order amount = 500.0)
- GET /health: Service health check

OpenAPI:
- See openapi/promotion.yaml for the specification.

Run locally:
1. Create and activate your Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Start server: `uvicorn app.main:app --host 0.0.0.0 --port 8108`

Notes:
- No environment variables are required for the MVP.
- In a future iteration, extend PromotionValidationRequest to include order amount and delivery fee details to compute precise discounts.
