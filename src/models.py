from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class BusinessLead(BaseModel):
    business_name: str
    product_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    category: Optional[str] = None
    source_url: str
    date_collected: str
    has_website: bool = False

    @validator('phone', pre=True)
    def clean_phone(cls, v):
        if not v:
            return None
        # Remove non-numeric characters except +
        clean = re.sub(r'[^\d+]', '', str(v))
        # Ensure it starts with +91 if it's an Indian number and 10 digits
        if len(clean) == 10 and clean.isdigit():
             return f"+91{clean}"
        elif len(clean) == 12 and clean.startswith('91'):
             return f"+{clean}"
        return clean

    @validator('website', pre=True)
    def clean_website(cls, v):
        if not v:
            return None
        if not v.startswith('http'):
            return f"https://{v}"
        return v

    @validator('reviews', pre=True)
    def clean_reviews(cls, v):
        if not v:
            return None
        # Extract digits
        clean = re.sub(r'[^\d]', '', str(v))
        if clean:
            return int(clean)
        return None

    @validator('rating', pre=True)
    def clean_rating(cls, v):
        if not v:
            return None
        # Extract float-like pattern
        match = re.search(r'\d+(\.\d+)?', str(v))
        if match:
             return float(match.group())
        return None
