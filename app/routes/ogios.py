from fastapi import APIRouter, HTTPException
from app.database.connection import db  # replace with your actual DB connection import
from bson import ObjectId
from app.schemas.ogios import Ogios,OgiosProductRow
import random
import re
from datetime import datetime
router = APIRouter()

@router.get("/")
def get_all_ogios():
    try:
        ogios_collection = db["ogios"]
        ogios = list(ogios_collection.find({}, {"_id": 0}))  # Exclude '_id' field
        if not ogios:
            return {"message": "No ogios found."}
        return {"ogios": ogios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    




@router.get("/sku/{sku}")
def get_ogio_by_sku(sku: str):
    try:
        ogios_collection = db["ogios"]
        ogio = ogios_collection.find_one({"sku": sku}, {"_id": 0})  # Exclude MongoDB '_id'

        if not ogio:
            raise HTTPException(status_code=404, detail="Ogio not found with the given SKU.")
        return {"ogio": ogio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
# updating the ogios data
# Update an ogio by its SKU


@router.put("/sku/{sku}")
def update_ogio(sku: str, updated_data: Ogios):
    ogios_collection = db["ogios"]

    # Check if document exists
    existing = ogios_collection.find_one({"sku": sku})
    if not existing:
        raise HTTPException(status_code=404, detail="Ogio not found.")

    # Convert incoming data to dict and remove 'sku'
    update_dict = updated_data.dict()
    update_dict.pop("sku", None)  #  This line prevents sku from being updated

    # Validate fields (excluding 'name')
    for key, value in update_dict.items():
        if key == "name":
            continue
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise HTTPException(status_code=400, detail=f"Field '{key}' cannot be empty or null.")

    # Remove non-essential fields for comparison
    exclude_fields = {"_id", "name", "updatedAt", "createdAt"}
    existing_filtered = {k: existing[k] for k in update_dict if k not in exclude_fields and k in existing}
    update_filtered = {k: update_dict[k] for k in existing_filtered}

    # Normalize values for strict comparison
    for key in update_filtered:
        if isinstance(update_filtered[key], float) and isinstance(existing_filtered[key], int):
            existing_filtered[key] = float(existing_filtered[key])

    if update_filtered == existing_filtered:
        raise HTTPException(status_code=400, detail="No changes detected. Same data cannot be updated.")

    # Add updatedAt timestamp and update
    update_dict["updatedAt"] = datetime.utcnow()
    ogios_collection.update_one({"sku": sku}, {"$set": update_dict})

    return {"message": "Ogio updated successfully."}

# create ogios data
@router.post("/create")
def create_ogio(ogio: Ogios):
    ogios_collection = db["ogios"]

    # Define the SKU prefix
    base_sku_suffix = "OG"
    start_number = 5924054

    # Get the last ogio with a valid numeric prefix in SKU
    last_ogio = ogios_collection.find_one(
        {"sku": {"$regex": r"^\d+OG$"}},
        sort=[("sku", -1)]
    )

    if last_ogio:
        # Extract numeric part from SKU
        match = re.match(r"^(\d+)", last_ogio["sku"])
        if match:
            last_number = int(match.group(1))
            new_number = last_number + 1
        else:
            raise HTTPException(status_code=400, detail="Invalid SKU format in database.")
    else:
        new_number = start_number

    # Generate new SKU
    new_sku = f"{new_number}{base_sku_suffix}"
    ogio.sku = new_sku

    # Add createdAt and updatedAt timestamps
    new_ogio = ogio.dict()
    new_ogio["createdAt"] = datetime.utcnow()
    new_ogio["updatedAt"] = datetime.utcnow()

    try:
        # Double-check that SKU is unique
        if ogios_collection.find_one({"sku": new_sku}):
            raise HTTPException(status_code=400, detail="SKU already exists.")

        ogios_collection.insert_one(new_ogio)
        new_ogio.pop("_id", None)  # Remove internal MongoDB _id

        return {"message": "Ogio created successfully.", "ogio": new_ogio}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Ogio: {str(e)}")


# delete the ogios

@router.delete("/sku/{sku}")
def delete_ogio(sku: str):
    ogios_collection = db["ogios"]

    # Check if the document with the given SKU exists
    existing = ogios_collection.find_one({"sku": sku})
    if not existing:
        raise HTTPException(status_code=404, detail="Ogio not found.")

    # Perform the deletion
    result = ogios_collection.delete_one({"sku": sku})

    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete the Ogio.")

    return {"message": "Ogio deleted successfully."}



# validate the Ogios excelsheet
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import pandas as pd
import io

from app.schemas.ogios import validate_product_excel

@router.post("/validate_ogios_excel/")
async def validate_ogios_excel_endpoint(
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

    corrected_df, logs = validate_product_excel(df)

    output = io.BytesIO()
    corrected_df.to_excel(output, index=False)
    output.seek(0)

    corrected_filename = f"{file.filename.rsplit('.', 1)[0]}_corrected.xlsx"

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