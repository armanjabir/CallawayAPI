from fastapi import APIRouter, HTTPException
from app.database.connection import db
from fastapi.responses import JSONResponse
from app.schemas.hardgoods import Hardgood,HardgoodsProductRow
from datetime import datetime
import re

from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import pandas as pd
import io

from app.schemas.hardgoods import validate_product_excel

router = APIRouter()
# fetching all hardgoods
@router.get("/")
def get_all_hardgoods():
    try:
        hardgoods_collection = db["hardgoods"]
        hardgoods = list(hardgoods_collection.find({}, {"_id": 0}))  # Exclude '_id' field
        if not hardgoods:
            return {"message": "No hardgoods found."}
        return {"hardgoods": hardgoods}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

# creating the hardgoods 




@router.post("/create")
def create_hardgood(hardgood: Hardgood):
    hardgoods_collection = db["hardgoods"]
    try:
        # Find the last hardgood entry by sorting by SKU in descending order
        last_hardgood = hardgoods_collection.find_one(sort=[("sku", -1)])

        # Default starting SKU if no items exist
        if not last_hardgood:
            new_sku_number = 641935800  # Start from a base number, adjust as necessary
        else:
            # Extract the numeric part from the SKU and increment it
            try:
                sku_match = re.match(r"(\d+)", last_hardgood["sku"])
                if sku_match:
                    last_sku_number = int(sku_match.group(1))  # Extract the number from SKU
                    new_sku_number = last_sku_number + 1
                else:
                    raise HTTPException(status_code=400, detail="Invalid SKU format in DB.")
            except Exception as e:
                raise HTTPException(status_code=400, detail="Error processing SKU format in DB.")

        # Create the new SKU string (You can customize the format)
        new_sku = str(new_sku_number)

        # Prepare data to insert into the database
        data = hardgood.dict()
        data["sku"] = new_sku
        data["createdAt"] = datetime.utcnow()
        data["updatedAt"] = datetime.utcnow()

        # Insert the new hardgood
        hardgoods_collection.insert_one(data)

        # Remove MongoDB's _id field from the response
        data.pop("_id", None)
        return {"message": "Hardgood created successfully", "hardgood": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating hardgood: {str(e)}")
# fetching the hardgoods new by it's sku:

@router.get("/sku/{sku}")
def get_hardgood_by_sku(sku: str):
    hardgoods_collection = db["hardgoods"]
    try:
        # Look for the item with the given SKU
        hardgood = hardgoods_collection.find_one({"sku": sku}, {"_id": 0})

        if not hardgood:
            raise HTTPException(status_code=404, detail="Hardgood not found with this SKU.")

        return {"hardgood": hardgood}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching hardgood: {str(e)}")



# deleting the hardgoods by it's id:
@router.delete("/{hardgood_id}")
async def delete_hardgood_by_id(hardgood_id: int):
    try:
        hardgoods_collection = db["hardgoods"]

        # Attempt to delete the hardgood by its 'id'
        result = hardgoods_collection.delete_one({"id": hardgood_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Hardgood not found")

        return {"message": "Hardgood deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting hardgood: {str(e)}")
    

# updaate the hardgoods by sku  :
@router.put("/update/{sku}")
async def update_hardgood(sku: str, updated_data: Hardgood):
    try:
        # Connect to the hardgoods collection
        hardgoods_collection = db["hardgoods"]

        # Check if the document with the given SKU exists
        existing_item = hardgoods_collection.find_one({"sku": sku})
        if not existing_item:
            raise HTTPException(status_code=404, detail="Hardgood item not found.")

        # Convert the incoming data to a dictionary
        update_dict = updated_data.dict(exclude_unset=True)  # Only include fields that are set

        # Validate fields to ensure they are not empty strings
        for key, value in update_dict.items():
            if value == "" or (isinstance(value, str) and value.strip() == ""):
                raise HTTPException(status_code=400, detail=f"Field '{key}' cannot be empty.")

        # Add the timestamp for the update
        update_dict["updatedAt"] = datetime.utcnow()

        # Compare the existing item with the new data to detect changes
        no_changes = True
        for key, value in update_dict.items():
            # Handle null/None values properly
            if existing_item.get(key) != value:
                no_changes = False
                break

        if no_changes:
            return {"message": "No changes detected."}

        # Perform the update in the database if changes are detected
        result = hardgoods_collection.update_one({"sku": sku}, {"$set": update_dict})

        # If no document was actually modified, it means the data was the same
        if result.modified_count == 0:
            return {"message": "No changes detected."}

        return {"message": "Hardgood item updated successfully", "sku": sku}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    



# validate sheet of the hardgoods




@router.post("/validate_hardgoods_excel/")
async def validate_hardgoods_excel_endpoint(
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