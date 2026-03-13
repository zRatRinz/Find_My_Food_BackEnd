from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import BadRequestException, NotFoundException
from app.routes import (
    recipeRoute, userRoute, authRoute, shoppingCartRoute, unitRoute, recipeAIRoute, userStockRoute, supportRoute, notificationRoute,
    scriptRoute
)

app = FastAPI()

@app.get("/health", tags=["health"])
async def health_check():
    return {"message": "Hello Thailand"}

app.include_router(recipeRoute.router)
app.include_router(userRoute.router)
app.include_router(authRoute.router)
app.include_router(shoppingCartRoute.router)
app.include_router(unitRoute.router)
app.include_router(recipeAIRoute.router)
app.include_router(userStockRoute.router)
app.include_router(supportRoute.router)
app.include_router(notificationRoute.router)
app.include_router(scriptRoute.router)

@app.exception_handler(404)
async def custom_not_found_handler(request,ex):
    return JSONResponse(
        status_code=404,
        content={
            "status":"fail",
            "message":"API Not Found",
            "data":None
        }
    )

@app.exception_handler(BadRequestException)
async def bad_request_handler(request: Request, ex: BadRequestException):
    return JSONResponse(
        status_code=400,
        content={
            "status": "fail",
            "message": str(ex),
            "data": None
        }
    )

@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, ex: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={
            "status": "fail",
            "message": str(ex),
            "data": None
        }
    )

@app.exception_handler(RequestValidationError)
async def custom_validation_data_handler(request, ex):
    return JSONResponse(
        status_code=422,
        content={
            "status": "fail",
            "message": "ข้อมูลที่ส่งมาไม่ถูกต้อง",
            "data": None
        },
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, ex: HTTPException):
    return JSONResponse(
        status_code = ex.status_code,
        content = {
            "status" : "fail",
            "message" : ex.detail,
            "data" : None
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, ex: Exception):
    print(f"System Crash: {str(ex)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "fail",
            "message": "เกิดข้อผิดพลาดที่ server กรุณาลองใหม่อีกครั้ง",
            "data": None
        }
    )