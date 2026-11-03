# backend/routers/upload.py (文件上传接口：云托管演示版，转为 Base64 返回)
import os
import uuid
import io
import base64
from PIL import Image
import filetype
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from core.security import get_current_user_id

router = APIRouter(prefix="/api/upload", tags=["upload"])

MAX_IMAGE_SIZE = 300 * 1024
MAX_PDF_SIZE = 2 * 1024 * 1024
MAX_IMAGE_PIXELS = 4096 * 4096


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
                raise HTTPException(status_code=400, detail="图片分辨率过大 (错误码: 40006)")

            data = list(img.getdata())
            img_without_exif = Image.new(img.mode, img.size)
            img_without_exif.putdata(data)

            out_io = io.BytesIO()
            img_without_exif.save(out_io, format="JPEG", quality=85)
            final_bytes = out_io.getvalue()
            mime = "image/jpeg"
        except Exception:
            raise HTTPException(status_code=400, detail="图片处理失败 (错误码: 40007)")

    elif mime == "application/pdf":
        if size > MAX_PDF_SIZE:
            raise HTTPException(status_code=400, detail="PDF 文件不能超过 2MB (错误码: 40002)")
        final_bytes = contents
    else:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/PDF 格式 (错误码: 40003)")

    # 🚨 修复硬伤：转为 Base64 Data URL 返回
    encoded_string = base64.b64encode(final_bytes).decode('utf-8')
    data_url = f"data:{mime};base64,{encoded_string}"

    return {"code": 0, "message": "上传成功", "url": data_url}