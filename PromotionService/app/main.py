from datetime import datetime, timezone
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class Promotion(BaseModel):
    """Represents a promotion/coupon configuration."""
    id: str = Field(..., description="Unique identifier of the promotion")
    code: str = Field(..., description="Coupon/promo code")
    type: str = Field(..., description="Type of promotion: percentage, fixed, or free_delivery")
    value: float = Field(..., description="Numeric discount value. For free_delivery, value is 0")
    minOrderValue: Optional[float] = Field(None, description="Minimum order value for eligibility")
    maxDiscount: Optional[float] = Field(None, description="Maximum discount allowed for percentage type")
    validFrom: Optional[datetime] = Field(None, description="Start of validity window (UTC)")
    validTo: Optional[datetime] = Field(None, description="End of validity window (UTC)")
    active: bool = Field(..., description="Whether the promotion is currently active")


# PUBLIC_INTERFACE
class PromotionValidationRequest(BaseModel):
    """Request to validate a promotion for a given order."""
    code: str = Field(..., description="Promotion code provided by the user")
    orderId: str = Field(..., description="Associated order ID for tracking/context")


# PUBLIC_INTERFACE
class PromotionValidationResult(BaseModel):
    """Validation result and computed discount for the provided promotion code."""
    valid: bool = Field(..., description="Whether the promotion is valid")
    discount: float = Field(..., description="Calculated discount amount to apply")
    message: str = Field(..., description="Human-readable message describing the result")
    promotion: Optional[Promotion] = Field(None, description="Promotion details if valid")


def _utcnow() -> datetime:
    """Helper to return timezone-aware utcnow."""
    return datetime.now(timezone.utc)


def _in_window(now: datetime, start: Optional[datetime], end: Optional[datetime]) -> bool:
    """Return True if now is within [start, end] considering optional bounds."""
    if start and now < start:
        return False
    if end and now > end:
        return False
    return True


# In-memory hardcoded promotions for MVP
# Notes:
# - Percentage promotion respects maxDiscount if provided.
# - minOrderValue is checked when orderAmount is included (see below for default assumption).
PROMOTIONS: Dict[str, Promotion] = {
    "WELCOME10": Promotion(
        id="p1",
        code="WELCOME10",
        type="percentage",
        value=10.0,
        minOrderValue=200.0,
        maxDiscount=100.0,
        validFrom=None,
        validTo=None,
        active=True,
    ),
    "SAVE50": Promotion(
        id="p2",
        code="SAVE50",
        type="fixed",
        value=50.0,
        minOrderValue=249.0,
        maxDiscount=None,
        validFrom=None,
        validTo=None,
        active=True,
    ),
    "FREESHIP": Promotion(
        id="p3",
        code="FREESHIP",
        type="free_delivery",
        value=0.0,
        minOrderValue=None,
        maxDiscount=None,
        validFrom=None,
        validTo=None,
        active=True,
    ),
    "WEEKEND20": Promotion(
        id="p4",
        code="WEEKEND20",
        type="percentage",
        value=20.0,
        minOrderValue=300.0,
        maxDiscount=120.0,
        validFrom=None,
        validTo=None,
        active=False,  # Inactive example
    ),
}

app = FastAPI(
    title="Promotion Service API",
    description="Manages promotions, coupons, and validation.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Promotions", "description": "Promotion and coupon validation endpoints"},
    ],
)


# PUBLIC_INTERFACE
@app.post(
    "/promotions/validate",
    response_model=PromotionValidationResult,
    tags=["Promotions"],
    summary="Validate a promotion code for an order",
    responses={
        200: {"description": "Validation result"},
        404: {"description": "Invalid or expired promotion"},
    },
)
def validate_promotion(
    payload: PromotionValidationRequest = Body(
        ..., description="Promotion validation request"
    ),
    # Optional order amount can be passed in headers in future; for MVP, we assume 500.0
):
    """
    Validate a promotion code for an order.

    Parameters:
    - payload: PromotionValidationRequest
        - code: Promotion code to validate
        - orderId: Associated order identifier

    Returns:
    - PromotionValidationResult
        - valid: Whether the code is valid
        - discount: Calculated discount amount
        - message: Additional info for the client
        - promotion: Details of the promotion if valid

    Notes:
    - MVP uses a hardcoded promotion list.
    - Order amount is not provided by the request schema; for demonstration, we assume a default order amount of 500.0.
      In future iterations, the API can be extended to accept orderAmount for precise validation.
    """
    code = payload.code.strip().upper()
    promo = PROMOTIONS.get(code)
    if not promo:
        raise HTTPException(status_code=404, detail="Invalid promotion code")

    if not promo.active:
        raise HTTPException(status_code=404, detail="Promotion is inactive or expired")

    now = _utcnow()
    if not _in_window(now, promo.validFrom, promo.validTo):
        raise HTTPException(status_code=404, detail="Promotion is not valid at this time")

    # MVP assumption: fixed default order amount if not provided via schema
    assumed_order_amount = 500.0

    # Check min order value
    if promo.minOrderValue is not None and assumed_order_amount < promo.minOrderValue:
        raise HTTPException(
            status_code=404,
            detail=f"Minimum order value of {promo.minOrderValue:.2f} not met",
        )

    discount = 0.0
    message = "Promotion applied successfully"

    if promo.type == "percentage":
        discount = (promo.value / 100.0) * assumed_order_amount
        if promo.maxDiscount is not None:
            discount = min(discount, promo.maxDiscount)
    elif promo.type == "fixed":
        discount = promo.value
        discount = min(discount, assumed_order_amount)  # Avoid exceeding order total
    elif promo.type == "free_delivery":
        # For MVP, we assume a typical delivery charge and return it as discount
        # In production, this should be computed from the order/cart details.
        discount = 30.0
    else:
        raise HTTPException(status_code=404, detail="Unsupported promotion type")

    result = PromotionValidationResult(
        valid=True,
        discount=float(round(discount, 2)),
        message=message,
        promotion=promo,
    )
    return result


# PUBLIC_INTERFACE
@app.get(
    "/health",
    tags=["Promotions"],
    summary="Health check",
    description="Simple endpoint to confirm the service is running.",
)
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "PromotionService", "time": _utcnow().isoformat()}
