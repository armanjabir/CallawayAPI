# app/models/hardgood.py # or just validator if root is not used
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from pydantic import BaseModel, validator, StrictInt, StrictStr
from typing import List, Dict, Optional, Literal, Union
import re
from difflib import get_close_matches
class Hardgood(BaseModel):
    description: str
    brand_id: int
    product_type: str
    category: str
    product_model: str
    life_cycle: str
    orientation: str
    mrp: float
    gst: float
    stock_88: int
    primary_image_url: Optional[str] = None
    gallery_images_url: Optional[str] = None
    image_done: int
    has_image: int
    __v: Optional[int] = 0


# sheet validator



# -------------------- Schema --------------------
class HardgoodsProductRow(BaseModel):
    sku: str  # Accepts int or str but stores as str
    description: StrictStr
    category: StrictStr
    product_type: StrictStr
    product_model: StrictStr
    orientation: Union[Literal["Left Handed", "Right Handed"], Literal["NA"]] = "NA"
    gst: StrictInt = 0
    mrp: StrictInt = 0
    stock_88: StrictInt = 0
    
    @validator('sku', pre=True, always=True)
    def validate_sku(cls, v):
        if v is None or str(v).strip().lower() in {'nan', 'none', ''}:
            return 'Unknown'
        return str(v).strip()

    @validator('description', 'category', 'product_type', 'product_model', pre=True, always=True)
    def validate_string_fields(cls, v, field):
        if v is None or str(v).strip().lower() in {'nan', 'none', ''}:
            return 'Unknown'
        if not isinstance(v, str):
            raise ValueError(f"Field '{field.name}' must be a string. Got {type(v).__name__}.")
        return v.strip()

    @validator('gst', 'mrp', 'stock_88', pre=True)
    def default_zero_if_invalid(cls, v):
        try:
            return int(float(str(v)))
        except:
            return 0

    @validator('orientation', pre=True, always=True)
    def normalize_orientation(cls, v):
        if isinstance(v, str):
            v = v.strip().title()
        if v not in ['Left Handed', 'Right Handed']:
            raise ValueError("Invalid orientation. Only 'Left Handed' or 'Right Handed' allowed.")
        return v

# -------------------- Aliases --------------------
COLUMN_ALIASES: Dict[str, List[str]] = {
    'sku': [r'sku.*'],
    'description': [r'desc.*', r'description.*'],
    'category': [r'category.*'],
    'product_type': [r'product[\s_]*type.*', r'type.*'],
    'product_model': [r'product[\s_]*model.*', r'model.*'],
    'orientation': [r'orientation.*', r'handed.*'],
    'gst': [r'^gst.*'],
    'mrp': [r'^mrp.*'],
    'stock_88': [r'stock[\s_]*88.*', r'stock 88.*'],
}

def match_column_name(col: str, aliases: Dict[str, List[str]]) -> Optional[str]:
    col_clean = col.strip().lower()
    for canonical_name, patterns in aliases.items():
        for pattern in patterns:
            if re.fullmatch(pattern, col_clean):
                return canonical_name
    return None

# -------------------- Validation Logic --------------------
def validate_product_excel(df: pd.DataFrame) -> (pd.DataFrame, List[str]):
    logs = []
    corrected_columns = {}
    canonical_fields = list(COLUMN_ALIASES.keys())

    # Match and map columns
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

    # Rename and filter columns
    df = df.rename(columns=corrected_columns)
    valid_cols = list(corrected_columns.values())
    df = df[valid_cols]

    validated_rows = []
    for index, row in df.iterrows():
        raw_data = row.to_dict()
        row_dict = {}

        for key in HardgoodsProductRow.__annotations__.keys():
            value = raw_data.get(key, "")

            # Handle orientation early for fallback
            if key == 'orientation':
                value_clean = str(value).strip().title()
                if value_clean not in ['Left Handed', 'Right Handed']:
                    logs.append(
                        f"Row {index + 2}: Invalid orientation value '{value}' — defaulting to 'NA'. Only 'Left Handed' or 'Right Handed' allowed."
                    )
                    value = 'NA'
                else:
                    value = value_clean
            elif key == 'description':
                if not isinstance(value, str) or str(value).strip().lower() in ["", "none", "nan"]:
                    logs.append(
                        f"Row {index + 2}: Invalid 'description' value '{value}' — defaulting to 'NA'."
                    )
                    value = 'NA'
                else:
                    value = str(value).strip()
            elif key == 'category':
                if not isinstance(value, str) or str(value).strip().lower() in ["", "none", "nan"]:
                    logs.append(
                        f"Row {index + 2}: Invalid 'category' value '{value}' — defaulting to 'NA'."
                    )
                    value = 'NA'
                else:
                    value = str(value).strip()

            elif key == 'product_type':
                if not isinstance(value, str) or str(value).strip().lower() in ["", "none", "nan"]:
                    logs.append(
                        f"Row {index + 2}: Invalid 'product_type' value '{value}' — defaulting to 'NA'."
                    )
                    value = 'NA'
                else:
                    value = str(value).strip()

            elif key == 'product_model':
                if not isinstance(value, str) or str(value).strip().lower() in ["", "none", "nan"]:
                    logs.append(
                        f"Row {index + 2}: Invalid 'product_model' value '{value}' — defaulting to 'NA'."
                    )
                    value = 'NA'
                else:
                    value = str(value).strip()
            elif key in ['stock_90', 'stock_88', 'gst', 'mrp']:
                try:
                    value = int(float(str(value)))
                except:
                    logs.append(f"Row {index + 2}: Invalid {key} value '{value}' — defaulting to 0.")
                    value = 0
                

            row_dict[key] = value

        try:
            validated = HardgoodsProductRow(**row_dict)
            validated_rows.append(validated.dict())
        except Exception as e:
            logs.append(f"Row {index + 2}: Validation error - {str(e)}")

    corrected_df = pd.DataFrame(validated_rows)
    return corrected_df, logs