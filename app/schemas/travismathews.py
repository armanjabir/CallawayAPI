from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, StrictStr, StrictInt, StrictFloat
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from pydantic import BaseModel, Field, StrictStr, StrictInt
from typing import Optional
from pydantic import BaseModel, EmailStr, StrictInt
from pydantic import BaseModel, StrictStr, StrictInt, Field
import re
import difflib
from pydantic import BaseModel, Field, StrictStr, StrictInt, conint,validator
import re
import pandas as pd
from difflib import get_close_matches
from pydantic import BaseModel, validator,StrictStr, StrictInt
from typing import List, Dict, Optional, Literal
from collections import defaultdict

class TravisMathew(BaseModel):
    brand_id: int
    color_code: str
    style_code: str
    size: str
    variation_sku: str
    name: Optional[str] = None
    description: str
    mrp: float
    gst: float
    length: Optional[str] = None
    stock_88: int
    stock_90: int
    category: str
    gender: str
    season: Optional[str] = None
    color: Optional[str] = None
    line: Optional[str] = None
    size_type: Optional[str] = None
    primary_image_url: Optional[str] = None
    gallery_images_url: Optional[str] = None
    has_image: int
    image_done: int






# -------------------- Schema for excel valiation of travismathews --------------------
class ProductRow(BaseModel):
    sku: StrictStr
    description: StrictStr
    category: StrictStr
    style_code: StrictStr
    color_code: StrictStr
    size: StrictStr
    season: StrictStr
    color: StrictStr
    length: StrictStr
    gender: Literal['Mens', 'Womens']
    line: Literal['Fashion', 'In Line', 'Core', 'Other']
    stock_90: StrictInt = 0
    stock_88: StrictInt = 0
    gst: StrictInt = 0
    mrp: StrictInt = 0
    variation_sku: List[StrictStr] = []
    primary_image_url: str
    gallery_images_url: Optional[str]

    @validator(
        'sku', 'description', 'category', 'style_code', 'color_code',
        'size', 'season', 'color', 'length', 'gender', 'line',
        pre=True, always=True
    )
    def default_string(cls, v):
        if v is None or str(v).strip().lower() in {'nan', 'none', ''}:
            return 'Unknown'
        return str(v).strip()

    @validator('stock_90', 'stock_88', 'gst', 'mrp', pre=True)
    def default_zero_if_invalid(cls, v):
        try:
            return int(float(str(v)))
        except:
            return 0
    @validator('description')
    def validate_description(cls, v):
        if not isinstance(v, str):
            raise ValueError("Description must be a string.")
        if any(char in v for char in ['@']):
            raise ValueError("Description contains invalid characters '@' which are not allowed.")
        return v

    @validator('variation_sku')
    def validate_variation_sku(cls, v, values):
        style_code = values.get('style_code')
        color_code = values.get('color_code')
        valid_sizes = {'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL'}

        if not style_code or not color_code:
            raise ValueError("style_code and color_code are required for variation_sku validation")

        base_prefix = f"{style_code}_{color_code}"

        if not isinstance(v, list):
            raise ValueError("variation_sku must be a list")

        invalid_skus = []
        for sku in v:
            if not sku.startswith(base_prefix):
                invalid_skus.append(sku)
                continue
            matched = any(re.search(rf"_{size}$", sku) for size in valid_sizes)
            if not matched:
                invalid_skus.append(sku)

        if invalid_skus:
            raise ValueError(
                f"Invalid variation_sku entries {invalid_skus}. Each SKU must start with '{base_prefix}' and end with a valid size."
            )

        return v
    # @validator('variation_sku')
    # def validate_variation_sku(cls, v, values):
    #     style_code = values.get('style_code')
    #     color_code = values.get('color_code')

    #     if not style_code or not color_code:
    #         raise ValueError("style_code and color_code are required for variation_sku validation")

    #     base_prefix = f"{style_code}_{color_code}"

    #     if not isinstance(v, list):
    #         raise ValueError("variation_sku must be a list")

    #     invalid_skus = [sku for sku in v if not sku.startswith(base_prefix)]

    #     if invalid_skus:
    #         raise ValueError(
    #             f"Invalid variation_sku entries {invalid_skus}. Each SKU must start with '{base_prefix}'."
    #         )

    #     return v
    @validator('primary_image_url')
    def validate_primary_image_url(cls, v, values):
        style_code = values.get('style_code')
        color_code = values.get('color_code')

        if not style_code or not color_code:
            raise ValueError("style_code and color_code are required to validate primary_image_url")

        base_prefix = f"{style_code}_{color_code}"
        valid_patterns = [
            f"{base_prefix}.jpg",
            f"{base_prefix}_A.jpg"
        ]

        if v not in valid_patterns:
            raise ValueError(
                f"primary_image_url must be one of {valid_patterns}, got '{v}'"
            )

        return v
    @validator("gallery_images_url")
    def validate_gallery_images_url(cls, v, values):
        if not v:
            return v

        style_code = values.get("style_code")
        color_code = values.get("color_code")
        if not style_code or not color_code:
            raise ValueError("Both style_code and color_code must be present for validating gallery_images_url")

        # Split by comma and validate each file
        images = [img.strip() for img in v.split(",")]

        for img in images:
            # Validate the pattern like: 1MY576_1WHT_A.jpg or 1MY576_1WHT_2.jpg
            if not re.fullmatch(rf"{style_code}_{color_code}_[A-D1-4]\.jpg", img):
                raise ValueError(f"Invalid gallery image filename: {img}")

        return v
    



# -------------------- Aliases --------------------
COLUMN_ALIASES: Dict[str, List[str]] = {
    'sku': [r'sku.*'],
    'description': [r'desc.*', r'description.*', r'descritption.*'],
    'category': [r'category.*', r'categories.*'],
    'season': [r'season.*'],
    'style_code': [r'style[\s_]*code.*', r'style_code.*', r'style code.*'],
    'color_code': [r'color[\s_]*code.*', r'color_code.*', r'color code.*'],
    'color': [r'^color.*'],
    'size': [r'^size.*'],
    'length': [r'^length.*'],
    'gender': [r'^gender.*'],
    'line': [r'^line.*'],
    'stock_90': [r'stock[\s_]*90.*', r'stock_90.*', r'stock 90.*'],
    'stock_88': [r'stock[\s_]*88.*', r'stock_88.*', r'stock 88.*'],
    'gst': [r'^gst.*'],
    'mrp': [r'^mrp.*'],
    'variation_sku': [r'variation.*sku.*'],
    "primary_image_url": [r"primary_image_url.*"],
    "gallery_images_url": [r"gallery[_\s]*images[_\s]*url.*"]
}

def match_column_name(col: str, aliases: Dict[str, List[str]]) -> Optional[str]:
    col_clean = col.strip().lower()
    for canonical_name, patterns in aliases.items():
        for pattern in patterns:
            if re.fullmatch(pattern, col_clean):
                return canonical_name
    return None

# -------------------- Main Validation --------------------
def validate_product_excel(df: pd.DataFrame) -> (pd.DataFrame, List[str]):
    logs = []
    corrected_columns = {}
    canonical_fields = list(COLUMN_ALIASES.keys())

    # Match and map columns
    for col in df.columns:
        matched = match_column_name(col, COLUMN_ALIASES)
        if matched:
            corrected_columns[col] = matched

            # Log suggestion if the original column is suspicious (fuzzy matched, not exact)
            if col.lower() != matched.lower():
                # Only log if it’s not an exact match like "category"
                logs.append(
                    f"Column '{col}' was accepted as '{matched}' — was this a typo?"
                )
        else:
            suggestion = get_close_matches(col.lower(), canonical_fields, n=1)
            if suggestion:
                logs.append(
                    f"Column '{col}' is unrecognized — did you mean '{suggestion[0]}'?"
                )
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
        skip_row = False

        for key in ProductRow.__annotations__.keys():
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
                    logs.append(
                        f"Row {index + 2}: Invalid gender value '{value}' — defaulting to 'Mens'. You can only select 'Mens' or 'Womens'."
                    )
                    value = 'Mens'
                else:
                    value = value_clean

            elif key == 'line':
                value_clean = str(value).strip()
                if value_clean not in ['Fashion', 'In Line', 'Core', 'Other']:
                    logs.append(
                        f"Row {index + 2}: Invalid line value '{value}' — defaulting to 'Other'. You can only select 'Fashion', 'Core', 'In Line', or 'Other'."
                    )
                    value = 'Other'
                else:
                    value = value_clean  # keep valid cleaned value
            elif key == 'length':
                value_clean = str(value).strip()
                if value_clean.lower() in {'', 'none', 'nan'}:
                    value = 'N/A'
                elif value_clean not in ['Half Sleeve', 'Full Sleeve']:
                    logs.append(
                        f"Row {index + 2}: Invalid length value '{value}' — defaulting to 'N/A'. Only 'Half Sleeve' or 'Full Sleeve' are accepted."
                    )
                    value = 'N/A'
                else:
                    value = value_clean  # keep valid cleaned value
            elif key == 'description':
                if not isinstance(value, str):
                    logs.append(f"Row {index + 2}: Invalid description value '{value}' — only strings are allowed. Row will be skipped.")
                    skip_row = True
                    break
                if any(char in value for char in ['@']):
                    logs.append(f"Row {index + 2}: Description contains invalid character in '{value}' — '@' are not allowed. Row will be skipped.")
                    skip_row = True
                    break
            elif key == 'variation_sku':
                if isinstance(value, str):
                    value = [sku.strip() for sku in value.split(',') if sku.strip()]
                elif not isinstance(value, list):
                    logs.append(f"Row {index + 2}: Invalid variation_sku format '{value}' — expected comma-separated string. Defaulting to empty list.")
                    value = []

            row_dict[key] = value

        if skip_row:
            continue

        try:
            validated = ProductRow(**row_dict)
            validated_rows.append(validated.dict())
        except Exception as e:
            logs.append(f"Row {index + 2}: Validation error - {str(e)}")

    corrected_df = pd.DataFrame(validated_rows)
    return corrected_df, logs