from fastapi import APIRouter, UploadFile, File
import shutil
import os

from app.services.report_analyzer import analyze_report

router = APIRouter(
    prefix="/report",
    tags=["Medical Report"]
)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
async def upload_report(file: UploadFile = File(...)):

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis = analyze_report(file_path)

    return {
        "message": "Report analyzed successfully.",
        "filename": file.filename,
        "analysis": analysis
    }