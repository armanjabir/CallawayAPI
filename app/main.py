from fastapi import FastAPI
from app.routes import user,hardgoods,ogios,orders,softgoods,travismathews

app = FastAPI()
# This method integrates an APIRouter instance into your main FastAPI application. It allows you to group related endpoints together, promoting a cleaner and more maintainable codebase
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(user.router, tags=["accountorders"])
app.include_router(hardgoods.router, prefix="/hardgoods", tags=["Hardgoods"])  # Added hardgoods route
app.include_router(ogios.router,prefix="/ogios",tags=["ogios"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(softgoods.router, prefix="/softgoods", tags=["softgoods"])
app.include_router(travismathews.router,prefix="/travismathews",tags=["travismathews"])

# @app.get("/")
# def home():
#     return {"message": "Welcome to the home page!"}
