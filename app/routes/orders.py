from fastapi import APIRouter,HTTPException
from app.database.connection import db  # adjust based on your structure
from bson.json_util import dumps
from app.schemas.orders import OrderCreate
import json
from uuid import uuid4
from pymongo import ReturnDocument
from typing import Optional
from typing import Optional, get_args, get_origin
router = APIRouter()

# get all orders
@router.get("/orders")
def get_all_orders():
    try:
        orders_collection = db["orders"]  # Access the orders collection from the db
        orders = list(orders_collection.find({}, {"_id": 0}))  # Exclude '_id' field
        if not orders:
            return {"message": "No orders found."}
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

# get order by id
@router.get("/{order_id}")
def get_order_by_id(order_id: int):  # Note: `int` because your "id" field is an integer
    try:
        orders_collection = db["orders"]

        # Find by custom "id" field, not MongoDB _id
        order = orders_collection.find_one({"id": order_id}, {"_id": 0})

        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")

        return {"order": order}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/{order_id}")
def delete_order_by_id(order_id: int):
    try:
        orders_collection = db["orders"]

        # Delete order by custom "id" field, not MongoDB _id
        result = orders_collection.find_one_and_delete({"id": order_id})

        if not result:
            raise HTTPException(status_code=404, detail="Order not found.")

        return {"detail": f"Order with id {order_id} has been deleted successfully."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# create orders
@router.post("/create")
def create_order(order: OrderCreate):
    orders_collection = db["orders"]
    try:
        # Convert request data to dictionary
        order_dict = order.dict()

        #  Get the last order with a valid integer `id` and increment it
        last_order = orders_collection.find_one(
            {"id": {"$type": "int"}},  # Ensure we only check documents where 'id' is an integer
            sort=[("id", -1)]
        )
        order_dict["id"] = last_order["id"] + 1 if last_order else 1

        # Parse JSON string fields into proper Python objects
        order_dict["items"] = json.loads(order_dict["items"])
        order_dict["retailer_details"] = json.loads(order_dict["retailer_details"])
        order_dict["manager_details"] = json.loads(order_dict["manager_details"])
        order_dict["salesRep_details"] = json.loads(order_dict["salesRep_details"])
        order_dict["note"] = json.loads(order_dict["note"])

        # Safety check: Avoid inserting duplicate ID (very rare due to above logic)
        existing_order = orders_collection.find_one({"id": order_dict["id"]})
        if existing_order:
            raise HTTPException(status_code=400, detail=f"Order with id {order_dict['id']} already exists.")

        # Insert the new order
        result = orders_collection.insert_one(order_dict)

        return {
            "message": "Order created successfully",
            "id": order_dict["id"]
        }

    except json.JSONDecodeError as json_err:
        raise HTTPException(status_code=400, detail=f"Invalid JSON string: {json_err}")
    except HTTPException:
        raise  # re-raise known HTTP errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# update orders
@router.put("/update/{order_id}")
def update_order(order_id: int, updated_order: OrderCreate):
    orders_collection = db["orders"]
    try:
        update_data = updated_order.dict()

        # Function to check if a field is optional
        def is_optional(field_type):
            return get_origin(field_type) is Optional or (type(None) in get_args(field_type))

        # Check only required fields for emptiness
        for field_name, field_type in OrderCreate.__annotations__.items():
            if field_name == "id":
                continue  # skip id, taken from URL
            if not is_optional(field_type):
                value = update_data.get(field_name)
                if value in [None, "", [], {}]:
                    raise HTTPException(status_code=400, detail=f"Field '{field_name}' is required and must not be empty.")

        # parse JSON strings
        update_data["items"] = json.loads(update_data["items"])
        update_data["retailer_details"] = json.loads(update_data["retailer_details"])
        update_data["manager_details"] = json.loads(update_data["manager_details"])
        update_data["salesRep_details"] = json.loads(update_data["salesRep_details"])
        update_data["note"] = json.loads(update_data["note"])

        update_data["id"] = order_id

        updated_doc = orders_collection.find_one_and_update(
            {"id": order_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if not updated_doc:
            raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found.")

        return {
            "message": "Order updated successfully",
            "id": updated_doc["id"]
        }

    except json.JSONDecodeError as json_err:
        raise HTTPException(status_code=400, detail=f"Invalid JSON string: {json_err}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")