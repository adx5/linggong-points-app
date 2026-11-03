# backend/routers/upload.py (文件上传接口：严格校验魔数、尺寸、大小，本地存储抽象)
import os
import uuid
import io
from PIL import Image
import filetype
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from core.security import get_current_user_id

router = APIRouter(prefix="/api/upload", tags=["upload"])

MAX_IMAGE_SIZE = 300 * 1024
MAX_PDF_SIZE = 2 * 1024 * 1024
MAX_IMAGE_PIXELS = 4096 * 4096


class StorageService:
    @staticmethod
    async def save(file_bytes: bytes, ext: str) -> str:
        os.makedirs("uploads", exist_ok=True)
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        filepath = f"uploads/{safe_filename}"
        with open(filepath, "wb") as f:
            f.write(file_bytes)
        return f"/uploads/{safe_filename}"


@router.post("")
async def upload_file(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    contents = await file.read()
    size = len(contents)

    kind = filetype.guess(contents)
    if not kind:
        raise HTTPException(status_code=400, detail="无法识别的文件类型或文件已损坏 (错误码: 40004)")

    mime = kind.mime
    ext = "." + kind.extension

    if mime.startswith("image/"):
        if size > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="图片大小不能超过 300KB，请压缩后重试 (错误码: 40002)")

        try:
            img = Image.open(io.BytesIO(contents))
            if img.width * img.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=400, detail="图片分辨率过大，拒绝解压炸弹 (错误码: 40006)")

            data = list(img.getdata())
            img_without_exif = Image.new(img.mode, img.size)
            img_without_exif.putdata(data)

            out_io = io.BytesIO()
            img_without_exif.save(out_io, format="JPEG", quality=85)
            final_bytes = out_io.getvalue()
            ext = ".jpg"
        except Exception:
            raise HTTPException(status_code=400, detail="图片处理失败，可能包含恶意数据 (错误码: 40007)")

    elif mime == "application/pdf":
        if size > MAX_PDF_SIZE:
            raise HTTPException(status_code=400, detail="PDF 文件不能超过 2MB (错误码: 40002)")
        final_bytes = contents

    else:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/PDF 格式 (错误码: 40003)")

    url = await StorageService.save(final_bytes, ext)
    return {"code": 0, "message": "上传成功", "url": url}