# backend/routers/upload.py (文件上传接口：接入图床、复检大小、防绕过、去EXIF)
import os
import uuid
import io
import httpx
from PIL import Image
import filetype
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from core.security import get_current_user_id

router = APIRouter(prefix="/api/upload", tags=["upload"])

MAX_IMAGE_SIZE = 300 * 1024
MAX_PDF_SIZE = 2 * 1024 * 1024
MAX_IMAGE_PIXELS = 4096 * 4096

# 🚨 环境变量控制：Demo 阶段严禁上传真实证件
ENABLE_VERIFY_UPLOAD = os.environ.get("ENABLE_VERIFY_UPLOAD", "false").lower() == "true"
BEEIMG_TOKEN = os.environ.get("BEEIMG_TOKEN")


async def upload_to_beeimg(file_bytes: bytes, filename: str) -> str:
    """封装图床上传，返回真实 URL"""
    if not BEEIMG_TOKEN:
        raise HTTPException(status_code=500, detail="服务端图床未配置，暂时无法上传")

    # 蜜蜂图床 API 接口 (以官方文档为准，此处为标准表单上传)
    url = "https://api.beeimg.com/api/v1/upload"
    headers = {"Authorization": f"Bearer {BEEIMG_TOKEN}"}
    files = {"file": (filename, file_bytes)}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, headers=headers, files=files, timeout=10.0)
            resp_data = resp.json()
            if resp.status_code == 200 and resp_data.get("code") == 0:
                return resp_data["data"]["url"]
            else:
                raise HTTPException(status_code=500, detail=f"图床上传失败: {resp_data.get('message')}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图床连接异常: {str(e)}")


@router.post("/normal")
async def upload_normal_image(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    """通用图片上传通道（如头像、环境照），严禁用于证件"""
    contents = await file.read()

    # 🚨 1. 魔数校验
    kind = filetype.guess(contents)
    if not kind or not kind.mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG 图片 (错误码: 40003)")

    # 🚨 2. 原始文件大小校验
    if len(contents) > MAX_IMAGE_SIZE * 2:  # 允许原图较大，交由下面压缩
        raise HTTPException(status_code=400, detail="原始图片过大，请压缩后重试 (错误码: 40002)")

    try:
        # 🚨 3. PIL 处理：去EXIF、防炸弹、透明底色转白
        img = Image.open(io.BytesIO(contents))
        if img.width * img.height > MAX_IMAGE_PIXELS:
            raise HTTPException(status_code=400, detail="图片分辨率过大 (错误码: 40006)")

        # 解决 PNG 透明背景转 JPEG 变黑的问题
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        else:
            img = img.convert("RGB")

        # 清理 EXIF
        data = list(img.getdata())
        img_clean = Image.new("RGB", img.size)
        img_clean.putdata(data)

        # 🚨 4. 重新保存并复检处理后的大小（硬伤 3）
        out_io = io.BytesIO()
        img_clean.save(out_io, format="JPEG", quality=85)
        final_bytes = out_io.getvalue()

        if len(final_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="图片处理后仍超过 300KB，拒绝上传 (错误码: 40002)")

    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=400, detail="图片处理失败，可能包含恶意数据 (错误码: 40007)")

    # 🚨 5. 强制使用 UUID，防路径穿越
    safe_filename = f"{uuid.uuid4().hex}.jpg"
    real_url = await upload_to_beeimg(final_bytes, safe_filename)

    return {"code": 0, "data": {"url": real_url}, "message": "上传成功"}


@router.post("/verify")
async def upload_verify_doc(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    """证件上传独立通道（硬伤 2：不再依赖前端 file_type）"""
    # 🚨 Demo 红线：环境变量未开启，绝对拦截
    if not ENABLE_VERIFY_UPLOAD:
        raise HTTPException(status_code=403, detail="Demo 测试环境，禁止上传真实证件！请使用‘仅供测试’假材料。")

    contents = await file.read()
    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="文件不能超过 2MB")

    kind = filetype.guess(contents)
    if not kind or kind.mime not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/PDF 格式")

    ext = ".jpg" if kind.mime == "image/jpeg" else (".png" if kind.mime == "image/png" else ".pdf")
    safe_filename = f"{uuid.uuid4().hex}{ext}"

    # 证件也需要真实上传到图床并返回 URL
    real_url = await upload_to_beeimg(contents, safe_filename)
    return {"code": 0, "data": {"url": real_url}, "message": "证件上传成功"}