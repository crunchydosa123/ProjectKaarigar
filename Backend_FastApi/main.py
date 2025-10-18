# app.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# import the router
from routes.video_edit import router as edit_router  # adjust import path if needed

logger = logging.getLogger("uvicorn.error")


def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Video Editor API")

    # CORS: same behavior as your Flask CORS line
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # default config values (you can override with env vars)
    app.state.MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 1024 * 1024 * 1024))
    upload_folder = os.environ.get("UPLOAD_FOLDER", os.path.join("/tmp", "uploads"))
    app.state.UPLOAD_FOLDER = upload_folder

    # ensure upload + ffmpeg bin dirs exist and adjust PATH
    @app.on_event("startup")
    def startup():
        os.makedirs(app.state.UPLOAD_FOLDER, exist_ok=True)
        ffmpeg_bin_dir = os.environ.get("FFMPEG_BIN_DIR", "/tmp/bin")
        os.makedirs(ffmpeg_bin_dir, exist_ok=True)
        os.environ["PATH"] = ffmpeg_bin_dir + ":" + os.environ.get("PATH", "")
        logger.info(f"Upload folder: {app.state.UPLOAD_FOLDER}; ffmpeg bin: {ffmpeg_bin_dir}")

    # register routers under /api
    app.include_router(edit_router, prefix="/api")

    @app.get("/", status_code=200)
    def index():
        return {"message": "FastAPI Video Editor API. Use POST /api/edit to upload video and user_prompt."}

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
