from fastapi import FastAPI, HTTPException, Request ,Depends,status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载.env 文件
load_dotenv()

# from fastapi_jwt_auth.exceptions import AuthJWTException

app = FastAPI()

# @app.exception_handler(AuthJWTException)
# def authjwt_exception_handler(request: Request, exc: AuthJWTException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.message}
#     )

# from .routers import auth2

from .routers import api
# from .routers.gradio import create_gradio_app
# import gradio as gr
# app.include_router(auth2.auth2)

app.include_router(api.api)

# app.mount("/upimg", create_gradio_app())
# io = gr.Interface(lambda x: "Hello, " + x + "!", "textbox", "textbox")
# app = gr.mount_gradio_app(app, io, path="/upimg")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"Hello": "World"}