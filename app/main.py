from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.routes import foodRoute, userRoute

app = FastAPI()

app.include_router(foodRoute.router)
app.include_router(userRoute.router)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code = exc.status_code,
        content = {
            "status" : "error",
            "message" : exc.detail,
            "data" : None
        }
    )

@app.exception_handler(404)
async def custom_not_found_handler(request,exc):
    return JSONResponse(
        status_code=404,
        content={
            "message":"API Not Found",
            "data":None
        }
    )

@app.exception_handler(RequestValidationError)
async def custom_validation_data_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "message": "ข้อมูลที่ส่งมาไม่ถูกต้อง",
            "data": None
        },
    )