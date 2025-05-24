from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from app.database.connection import db
from app.schemas.travismathews import TravisMathew
from datetime import datetime
from uuid import uuid4
import pandas as pd
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
import difflib
import pandas as pd
from typing import List
from fastapi import UploadFile, File, HTTPException, APIRouter
from pydantic import BaseModel
import re
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app.schemas.travismathews import validate_product_excel
from fastapi import UploadFile, File, APIRouter, Query
from fastapi.responses import StreamingResponse
import io
import pandas as pd


router = APIRouter()
@router.get("/")
def get_all_travismathews():
    travismathews_collection = db["travismathews"]
    try:
        travis_data = list(travismathews_collection.find({}, {"_id": 0}))  # Exclude '_id' field
        if not travis_data:
            return {"message": "No travismathews data found."}
        return {"travismathews": travis_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# get travismathews by it's sku

@router.get("/{sku}")
def get_travismathew_by_sku(sku: str):
    travismathews_collection = db["travismathews"]
    try:
        travis = travismathews_collection.find_one({"sku": sku}, {"_id": 0})  # Exclude '_id'
        if not travis:
            raise HTTPException(status_code=404, detail="Travismathew with this SKU not found")
        return {"travismathew": travis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

# create travismathews 

@router.post("/create")
def create_travismathew(data: TravisMathew):
    travismathews_collection = db["travismathews"]
    try:
        # Generate unique SKU: <style_code>_<color_code>_<size>
        generated_sku = f"{data.style_code}_{data.color_code}_{data.size}".upper()

        # Check if SKU already exists
        if travismathews_collection.find_one({"sku": generated_sku}):
            raise HTTPException(status_code=400, detail="SKU already exists")

        data_dict = data.dict()
        data_dict["sku"] = generated_sku
        data_dict["createdAt"] = datetime.utcnow()
        data_dict["updatedAt"] = datetime.utcnow()

        result = travismathews_collection.insert_one(data_dict)

        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create TravisMathew item")

        return {"message": "TravisMathew item created", "sku": generated_sku}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


#  updates the travismathews items
# Update method to modify the TravisMathew data by SKU
@router.put("/sku/{sku}")
async def update_travismathew(sku: str, updated_data: TravisMathew):
    try:
        # Assuming 'db' is the database connection and 'travismathews' is the collection name
        travismathews_collection = db["travismathews"]

        # Check if the document with the given SKU exists
        existing_item = travismathews_collection.find_one({"sku": sku})
        if not existing_item:
            raise HTTPException(status_code=404, detail="TravisMathew item not found.")

        # Convert the incoming data to a dictionary
        update_dict = updated_data.dict(exclude_unset=True)  # Use exclude_unset to exclude fields that were not provided

        # Validate fields to ensure they are not empty
        for key, value in update_dict.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                raise HTTPException(status_code=400, detail=f"Field '{key}' cannot be empty or null.")
            
        comparison_existing = {k: v for k, v in existing_item.items() if k in update_dict and k not in ["_id", "createdAt", "updatedAt"]}
        comparison_update = {k: v for k, v in update_dict.items() if k in comparison_existing}
        if comparison_existing == comparison_update:
            raise HTTPException(status_code=400, detail="No changes detected.")
        # Add the timestamp for the update
        update_dict["updatedAt"] = datetime.utcnow()

        # Perform the update in the database
        result = travismathews_collection.update_one({"sku": sku}, {"$set": update_dict})
        # Check if any document was updated
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes detected or update failed.")

        return {"message": "TravisMathew item updated successfully", "sku": sku}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

# delete travismathews items

@router.delete("/sku/{sku}")
async def delete_travismathew(sku: str):
    try:
        # Assuming 'db' is the database connection and 'travismathews' is the collection name
        travismathews_collection = db["travismathews"]

        # Check if the document with the given SKU exists
        existing_item = travismathews_collection.find_one({"sku": sku})
        if not existing_item:
            raise HTTPException(status_code=404, detail="TravisMathew item not found.")

        # Perform the delete operation
        result = travismathews_collection.delete_one({"sku": sku})

        # Check if any document was deleted
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Delete operation failed.")

        return {"message": "TravisMathew item deleted successfully", "sku": sku}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    






@router.post("/validate_excel/")
async def validate_excel(
    file: UploadFile = File(...),
    download: bool = Query(False, description="Set to true to download corrected Excel file")
):
    if not file.filename.endswith((".xls", ".xlsx")):
        return {"error": "Only Excel files are supported"}

    content = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        return {"error": f"Error reading Excel file: {str(e)}"}

    # Validate the DataFrame using your existing logic
    corrected_df, logs = validate_product_excel(df)

    # Generate in-memory Excel file
    output = io.BytesIO()
    corrected_df.to_excel(output, index=False)
    output.seek(0)

    corrected_filename = f"{file.filename.split('.')[0]}_corrected.xlsx"

    # If download requested, return the file directly
    if download:
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={corrected_filename}"
            }
        )

    # Otherwise return JSON with logs and file name
    return {
        "message": "Validation completed",
        "issues": logs,
        "corrected_file": corrected_filename
    }






