# backend/routers/upload.py (满足合规要求的存储抽象版)
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

# 🚨 严格从环境变量读取，默认关闭证件上传
ENABLE_VERIFY_UPLOAD = os.environ.get("ENABLE_VERIFY_UPLOAD", "false").lower() == "true"

BEEIMG_TOKEN = os.environ.get("BEEIMG_TOKEN")
BEEIMG_UPLOAD_URL = os.environ.get("BEE_IMAGE_HOST_API", "https://www.beeimg.cn/api/v2/upload")
BEEIMG_STORAGE_ID = os.environ.get("BEEIMG_STORAGE_ID")


class StorageProvider:
    """存储提供者抽象基类：上线前只需替换此类的实现即可切换到 OSS"""

    async def upload(self, file_bytes: bytes, filename: str) -> str:
        raise NotImplementedError


class BeeImgStorage(StorageProvider):
    """蜜蜂图床实现 (开发期临时隔离手段)"""

    async def _get_storage_id(self, client: httpx.AsyncClient) -> int:
        if BEEIMG_STORAGE_ID:
            return int(BEEIMG_STORAGE_ID)
        if not BEEIMG_TOKEN:
            raise HTTPException(status_code=503, detail="存储服务未配置，请联系管理员")

        try:
            group_url = "https://www.beeimg.cn/api/v2/group"
            resp = await client.get(group_url, headers={"Authorization": f"Bearer {BEEIMG_TOKEN}"}, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success" and data.get("data"):
                    storages = data["data"].get("storages", [])
                    if storages:
                        return storages[0]["id"]
        except Exception as e:
            print(f"⚠️ 图床获取 storage_id 异常: {e}")

        raise HTTPException(status_code=503, detail="图床服务未就绪 (storage_id 获取失败)，请稍后再试")

    async def upload(self, file_bytes: bytes, filename: str) -> str:
        if not BEEIMG_TOKEN:
            raise HTTPException(status_code=503, detail="服务端未配置存储凭证")

        async with httpx.AsyncClient() as client:
            storage_id = await self._get_storage_id(client)
            headers = {"Authorization": f"Bearer {BEEIMG_TOKEN}"}
            files = {"file": (filename, file_bytes)}
            data = {"storage_id": str(storage_id)}

            try:
                resp = await client.post(BEEIMG_UPLOAD_URL, headers=headers, files=files, data=data, timeout=20.0)
                resp_data = resp.json()

                if resp.status_code == 200 and resp_data.get("status") == "success":
                    public_url = resp_data.get("data", {}).get("public_url")
                    if public_url:
                        return public_url
                    raise HTTPException(status_code=502, detail="图床返回格式异常")
                else:
                    error_msg = resp_data.get("message", "未知错误")
                    if "空间不足" in error_msg:
                        raise HTTPException(status_code=400, detail="图床储存空间已满，请联系管理员清理")
                    raise HTTPException(status_code=400, detail=f"图床上传失败: {error_msg}")
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail="上传图床超时，请重试")
            except Exception as e:
                if isinstance(e, HTTPException): raise e
                raise HTTPException(status_code=500, detail="存储服务连接异常")


# 未来切 OSS 时： storage_provider = AliyunOssStorage()
storage_provider = BeeImgStorage()


async def process_and_upload(file: UploadFile, is_verify: bool = False) -> str:
    contents = await file.read()
    if is_verify and not ENABLE_VERIFY_UPLOAD:
        raise HTTPException(status_code=403, detail="Demo 测试环境，禁止上传真实证件！请使用仅供测试假材料。")

    kind = filetype.guess(contents)
    if not kind: raise HTTPException(status_code=400, detail="无法识别文件类型")

    if kind.mime.startswith("image/"):
        if len(contents) > MAX_IMAGE_SIZE * 2:
            raise HTTPException(status_code=400, detail="原始图片过大")

        try:
            img = Image.open(io.BytesIO(contents))
            if img.width * img.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=400, detail="图片分辨率过大")

            # 透明底转白
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            else:
                img = img.convert("RGB")

            out_io = io.BytesIO()
            img.save(out_io, format="JPEG", quality=85)
            final_bytes = out_io.getvalue()

            if len(final_bytes) > MAX_IMAGE_SIZE:
                raise HTTPException(status_code=400, detail="图片处理后超过 300KB")

            ext = ".jpg"
        except Exception:
            raise HTTPException(status_code=400, detail="图片安全校验失败")
    elif kind.mime == "application/pdf":
        if len(contents) > MAX_PDF_SIZE:
            raise HTTPException(status_code=400, detail="PDF 不能超过 2MB")
        final_bytes = contents
        ext = ".pdf"
    else:
        raise HTTPException(status_code=400, detail="仅支持图片或PDF")

    safe_filename = f"{uuid.uuid4().hex}{ext}"
    return await storage_provider.upload(final_bytes, safe_filename)


@router.post("/normal")
async def upload_normal_image(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    url = await process_and_upload(file, is_verify=False)
    return {"code": 0, "data": {"url": url}, "message": "上传成功"}


@router.post("/verify")
async def upload_verify_doc(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    url = await process_and_upload(file, is_verify=True)
    return {"code": 0, "data": {"url": url}, "message": "证件上传成功"}