from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OrderCreate(BaseModel):
    id: Optional[int] = None
    user_id: int
    brand_id: int
    order_date: datetime
    items: str  # JSON string
    discount_type: str
    discount_percent: str
    discount_amount: str
    total_val_pre_discount: str
    total_value: str
    status: str
    manager_id: int
    retailer_id: int
    salesrep_id: int
    created_at: datetime
    updated_at: datetime
    createdAt: datetime
    updatedAt: datetime
    retailer_details: str  # JSON string
    manager_details: str   # JSON string
    salesRep_details: str  # JSON string
    manager_name: str
    note: str  # JSON string
    retailer_address: str
    retailer_gstin: str
    retailer_name: str
    retailer_phone: Optional[str] = None
    salesrep_name: str