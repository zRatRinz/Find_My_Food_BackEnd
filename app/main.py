from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware

from app.routes import recipeRoute, userRoute, authRoute, shoppingCartRoute, unitRoute, recipeAIRoute

app = FastAPI()

SECRET_KEY = "TestSecretKey"
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.get("/health", tags=["health"])
async def health_check():
    return {"message": "Hello Thailand"}

app.include_router(recipeRoute.router)
app.include_router(userRoute.router)
app.include_router(authRoute.router)
app.include_router(shoppingCartRoute.router)
app.include_router(unitRoute.router)
app.include_router(recipeAIRoute.router)

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