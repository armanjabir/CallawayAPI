from pydantic import BaseModel, Field
from typing import Optional
import re
from typing import List, Dict, Optional, Literal
import pandas as pd
from difflib import get_close_matches
from pydantic import BaseModel, validator, StrictStr, StrictInt

class Softgood(BaseModel):
    sku: str
    description: str
    brand_id: int
    mrp: float
    gst: int
    size: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    series: Optional[str] = None
    type: Optional[str] = None
    style_id: Optional[str] = None
    season: Optional[str] = None
    sleeves: Optional[str] = None
    stock_88: int
    stock_90: int
    primary_image_url: Optional[str] = None
    gallery_images_url: Optional[str] = None
    image_done: Optional[int] = 0
    has_image: Optional[int] = 0
    variation_sku: Optional[str] = ""
    __v: Optional[int] = 0




# --------------------------
# Column Matching Definitions
# --------------------------

COLUMN_ALIASES = {
    'sku': [r'sku.*'],
    'description': [r'desc.*', r'description.*'],
    'category': [r'category.*'],
    'style_id': [r'style.*id.*'],
    'color': [r'color.*code.*'],
    'size': [r'^size.*'],
    'season': [r'^season.*'],
    'sleeves': [r'^sleeves?$', r'sleeve.*type.*', r'^sleeve.*'],
    'color': [r'^color$'],
    'gender': [r'^gender.*'],
    'stock_90': [r'stock[\s_]*90.*'],
    'stock_88': [r'stock[\s_]*88.*'],
    'gst': [r'^gst.*'],
    'mrp': [r'^mrp.*'],
}


def match_column_name(col: str, aliases: Dict[str, List[str]]) -> Optional[str]:
    """Match a column name to the closest canonical field using regex patterns."""
    col_clean = col.strip().lower()
    for canonical_name, patterns in aliases.items():
        for pattern in patterns:
            if re.fullmatch(pattern, col_clean):
                return canonical_name
    return None

# --------------------------
# Pydantic Validation Schema
# --------------------------

class CallawayProductRow(BaseModel):
    sku: StrictInt
    description: StrictStr
    category: StrictStr
    style_id: StrictStr
    color: StrictStr
    size: StrictStr
    season: StrictStr
    sleeves:StrictStr
    gender: Literal['Mens', 'Womens']
    stock_90: StrictInt = 0
    stock_88: StrictInt = 0
    gst: StrictInt = 0
    mrp: StrictInt = 0


    @validator('sku', pre=True)
    def validate_sku(cls, v):
        try:
            val = int(str(v).strip())
            if val < 0:
                raise ValueError("SKU must be a non-negative integer.")
            return val
        except Exception:
            raise ValueError("SKU must be a valid integer.")

    @validator(
        'description', 'category', 'style_id',"sleeves",
        'size', 'season', 'color',
        pre=True, always=True
    )
    def default_string(cls, v):
        if v is None or str(v).strip().lower() in {'nan', 'none', ''}:
            return 'N/A'
        return str(v).strip()

    @validator('stock_90', 'stock_88', 'gst', 'mrp', pre=True)
    def default_zero_if_invalid(cls, v):    
        try:
            return int(float(str(v)))
        except:
            return 0

# --------------------------
# Excel Validation Logic
# --------------------------

def validate_callaway_excel(df: pd.DataFrame) -> (pd.DataFrame, List[str]):
    logs = []
    corrected_columns = {}
    canonical_fields = list(COLUMN_ALIASES.keys())

    for col in df.columns:
        matched = match_column_name(col, COLUMN_ALIASES)
        if matched:
            corrected_columns[col] = matched
            if col.lower() != matched.lower():
                logs.append(f"Column '{col}' was accepted as '{matched}' — was this a typo?")
        else:
            suggestion = get_close_matches(col.lower(), canonical_fields, n=1)
            if suggestion:
                logs.append(f"Column '{col}' is unrecognized — did you mean '{suggestion[0]}'?")
            else:
                logs.append(f"Unrecognized column: '{col}' — column will be ignored.")

    # Rename and filter DataFrame
    df = df.rename(columns=corrected_columns)
    valid_cols = list(corrected_columns.values())
    df = df[valid_cols]

    validated_rows = []

    for index, row in df.iterrows():
        raw_data = row.to_dict()
        row_dict = {}
        skip_row = False

        for key in CallawayProductRow.__annotations__.keys():
            value = raw_data.get(key, "")

            if key in ['stock_90', 'stock_88', 'gst', 'mrp']:
                try:
                    value = int(float(str(value)))
                except:
                    logs.append(f"Row {index + 2}: Invalid {key} value '{value}' — defaulting to 0.")
                    value = 0

            elif key == 'gender':
                value_clean = str(value).strip()
                if value_clean not in ['Mens', 'Womens']:
                    logs.append(f"Row {index + 2}: Invalid gender value '{value}' — defaulting to 'Mens'.")
                    value = 'Mens'
                else:
                    value = value_clean

            elif key == 'description':
                if not isinstance(value, str):
                    logs.append(f"Row {index + 2}: Description must be a string. Row skipped.")
                    skip_row = True
                    break
                if '@' in value:
                    logs.append(f"Row {index + 2}: Description contains '@'. Row skipped.")
                    skip_row = True
                    break

            row_dict[key] = value

        if skip_row:
            continue

        try:
            validated = CallawayProductRow(**row_dict)
            validated_rows.append(validated.dict())
        except Exception as e:
            logs.append(f"Row {index + 2}: Validation error - {str(e)}")

    return pd.DataFrame(validated_rows), logs