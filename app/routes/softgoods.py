from fastapi import APIRouter, HTTPException
from app.database.connection import db  # your MongoDB collection
from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.softgoods import Softgood,CallawayProductRow
import uuid
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from app.schemas.softgoods import validate_callaway_excel
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from app.schemas.softgoods import validate_callaway_excel
# your Pydantic model for Softgoods

router = APIRouter()

@router.get("/")
def get_all_softgoods():
    try:
        softgoods_collection = db["softgoods"]
        softgoods = list(softgoods_collection.find({}, {"_id": 0}))  # Exclude '_id' field
        if not softgoods:
            return {"message": "No softgoods found."}
        return {"softgoods  ": softgoods}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
#  fetch all softgoods with the sku

@router.get("/{sku}")
def get_softgood_by_sku(sku: str):
    try:
        softgoods_collection = db["softgoods"]  # Get the collection explicitly
        softgood = softgoods_collection.find_one({"sku": sku}, {"_id": 0})  # Exclude MongoDB _id
        if not softgood:
            raise HTTPException(status_code=404, detail="Softgood with this SKU not found")
        return {"softgood": softgood}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/create")
async def create_softgood(softgood: dict):
    try:
        # Step 1: Auto-generate SKU
        # Example: Generating SKU using UUID and current timestamp
        new_sku = str(uuid.uuid4().hex[:8].upper()) + str(int(datetime.utcnow().timestamp()))

        # Step 2: Add the SKU to the softgood data
        softgood["sku"] = new_sku
        softgoods_collection = db["softgoods"]
        # Step 3: Insert the softgood into the collection
        result = softgoods_collection.insert_one(softgood)

        if result.inserted_id:
            return {"message": "Softgood created successfully", "sku": new_sku}
        else:
            raise HTTPException(status_code=500, detail="Error creating softgood")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



@router.put("/sku/{sku}")
def update_softgood(sku: str, updated_data: Softgood):
    softgoods_collection = db["softgoods"]

    # Fetch the existing softgood
    existing = softgoods_collection.find_one({"sku": sku})
    if not existing:
        raise HTTPException(status_code=404, detail="Softgood not found.")

    # Convert the incoming data to a dictionary
    update_dict = updated_data.dict()

    #  Never allow SKU to be updated
    if "sku" in update_dict:
        update_dict.pop("sku")

    #  Validation: prevent empty fields (only skip ones that were null originally)
    for key, value in update_dict.items():
        if existing.get(key) is None:
            continue  # field was null before, it's allowed
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise HTTPException(status_code=400, detail=f"Field '{key}' cannot be empty or null.")

  

    #  Check if any real changes were made
    exclude_fields = {"_id", "updatedAt", "createdAt"}
    existing_filtered = {k: existing[k] for k in update_dict if k not in exclude_fields and k in existing}
    update_filtered = {k: update_dict[k] for k in existing_filtered}

    for key in update_filtered:
        if isinstance(update_filtered[key], float) and isinstance(existing_filtered[key], int):
            existing_filtered[key] = float(existing_filtered[key])

    if update_filtered == existing_filtered:
        raise HTTPException(status_code=400, detail="No changes detected. Same data cannot be updated.")

    # Set updated timestamp
    update_dict["updatedAt"] = datetime.utcnow()

    # Perform update
    softgoods_collection.update_one({"sku": sku}, {"$set": update_dict})

    return {"message": "Softgood updated successfully."}

# delete the softgoods by the sku

@router.delete("/sku/{sku}")
def delete_softgood(sku: str):
    softgoods_collection = db["softgoods"]

    result = softgoods_collection.delete_one({"sku": sku})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Softgood not found.")

    return {"message": f"Softgood with SKU {sku} deleted successfully."}







@router.post("/validate_callaway_excel/")
async def validate_softgoods_endpoint(
    file: UploadFile = File(...),
    download: bool = Query(False)
):
    if not file.filename.endswith((".xls", ".xlsx")):
        return {"error": "Only Excel files are supported."}

    content = await file.read()

    try:
        df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        return {"error": f"Could not read Excel file: {str(e)}"}

    corrected_df, logs = validate_callaway_excel(df)

    output = io.BytesIO()
    corrected_df.to_excel(output, index=False)
    output.seek(0)

    corrected_filename = f"{file.filename.split('.')[0]}_corrected.xlsx"

    if download:
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={corrected_filename}"}
        )

    return {
        "message": "Validation completed.",
        "issues": logs,
        "corrected_file": corrected_filename
    }