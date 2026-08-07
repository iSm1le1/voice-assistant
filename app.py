"""程序入口：创建 FastAPI app、注册路由、挂静态页、启动 uvicorn。"""
import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.voice_api import router as voice_router
from config import settings
from utils.logger import setup_logger

# 初始化日志（config 导入时已校验密钥）
setup_logger()

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def create_app() -> FastAPI:
    app = FastAPI(title="语音 AI 助手", version="1.0")
    app.include_router(voice_router)
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=True)
