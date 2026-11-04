# backend/routers/upload.py (基于 BeeIMG 官方 v2 文档修正，完整版)
import os
import uuid
import io
import httpx
from PIL import Image
import filetype
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from core.security import get_current_user_id

router = APIRouter(prefix="/api/upload", tags=["upload"])

# 基础配置
MAX_IMAGE_SIZE = 300 * 1024  # 300KB
MAX_PDF_SIZE = 2 * 1024 * 1024  # 2MB
MAX_IMAGE_PIXELS = 4096 * 4096  # 防解压炸弹

# Demo 环境证件上传开关
ENABLE_VERIFY_UPLOAD = os.environ.get("ENABLE_VERIFY_UPLOAD", "false").lower() == "true"

# 🚨 BeeIMG 官方配置 (从环境变量读取，若未配置则使用默认值)
BEEIMG_TOKEN = os.environ.get("BEEIMG_TOKEN")
# 官方推荐 API 地址
BEEIMG_UPLOAD_URL = os.environ.get("BEE_IMAGE_HOST_API", "https://www.beeimg.cn/api/v2/upload")
# 若无法自动获取 storage_id，可在此手动指定作为兜底
BEEIMG_STORAGE_ID = os.environ.get("BEEIMG_STORAGE_ID")


async def _get_storage_id(client: httpx.AsyncClient) -> int:
    """
    调用 GET /group 接口获取有效的 storage_id。
    文档指出：storage_id 取 GET /group 返回的 storages[].id[reference:4]
    """
    # 1. 如果环境变量直接配置了，优先使用
    if BEEIMG_STORAGE_ID:
        return int(BEEIMG_STORAGE_ID)

    if not BEEIMG_TOKEN:
        raise HTTPException(status_code=500, detail="服务端缺少 BEEIMG_TOKEN 配置")

    # 2. 尝试调用 /group 动态获取
    try:
        # 注意：/group 接口的完整路径通常是 /api/v2/group，需与上传接口保持同源
        group_url = "https://www.beeimg.cn/api/v2/group"
        resp = await client.get(
            group_url,
            headers={"Authorization": f"Bearer {BEEIMG_TOKEN}"},
            timeout=10.0
        )
        if resp.status_code == 200:
            data = resp.json()
            # 文档说明 storages 是一个数组
            if data.get("status") == "success" and data.get("data"):
                storages = data["data"].get("storages", [])
                if storages:
                    return storages[0]["id"]
    except Exception as e:
        print(f"⚠️ 自动获取 storage_id 失败: {e}")

    # 3. 实在拿不到，抛出明确错误
    raise HTTPException(
        status_code=500,
        detail="无法获取图床 storage_id，请检查 BEEIMG_TOKEN 是否正确，或在环境变量中配置 BEEIMG_STORAGE_ID"
    )


async def upload_to_beeimg(file_bytes: bytes, filename: str) -> str:
    """封装 BeeIMG 上传，返回 public_url"""
    if not BEEIMG_TOKEN:
        raise HTTPException(status_code=500, detail="服务端图床未配置(缺少 BEEIMG_TOKEN)")

    async with httpx.AsyncClient() as client:
        # 1. 获取 storage_id
        storage_id = await _get_storage_id(client)

        # 2. 准备请求数据
        headers = {"Authorization": f"Bearer {BEEIMG_TOKEN}"}
        files = {"file": (filename, file_bytes)}
        data = {"storage_id": str(storage_id)}  # 文档要求必填[reference:5]

        try:
            # 3. 发起上传请求
            resp = await client.post(
                BEEIMG_UPLOAD_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=20.0
            )
            resp_data = resp.json()

            # 4. 解析响应 (文档：成功 status="success"，图片链接在 data.public_url)[reference:6]
            if resp.status_code == 200:
                if resp_data.get("status") == "success":
                    public_url = resp_data.get("data", {}).get("public_url")
                    if public_url:
                        return public_url
                    raise HTTPException(status_code=500, detail="图床返回成功但缺少 public_url 字段")
                else:
                    # 业务错误 (如空间不足、频率限制)
                    error_msg = resp_data.get("message", "未知错误")
                    # 文档中提到的“储存空间不足”提示[reference:7]
                    if "空间不足" in error_msg:
                        raise HTTPException(status_code=400, detail="图床储存空间不足，请清理后重试")
                    if "一分钟内" in error_msg:
                        raise HTTPException(status_code=429, detail=f"上传过于频繁: {error_msg}")
                    raise HTTPException(status_code=400, detail=f"图床上传失败: {error_msg}")
            else:
                raise HTTPException(status_code=500, detail=f"图床响应异常 HTTP {resp.status_code}")

        except httpx.ConnectError:
            raise HTTPException(status_code=500, detail="网络连接异常，无法访问图床服务器")
        except httpx.TimeoutException:
            raise HTTPException(status_code=500, detail="图床请求超时，请稍后重试")
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"图床连接异常: {str(e)}")


@router.post("/normal")
async def upload_normal_image(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    contents = await file.read()

    kind = filetype.guess(contents)
    if not kind or not kind.mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG 图片")

    if len(contents) > MAX_IMAGE_SIZE * 2:
        raise HTTPException(status_code=400, detail="原始图片过大，请压缩后重试")

    try:
        img = Image.open(io.BytesIO(contents))
        if img.width * img.height > MAX_IMAGE_PIXELS:
            raise HTTPException(status_code=400, detail="图片分辨率过大")

        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        else:
            img = img.convert("RGB")

        data = list(img.getdata())
        img_clean = Image.new("RGB", img.size)
        img_clean.putdata(data)

        out_io = io.BytesIO()
        img_clean.save(out_io, format="JPEG", quality=85)
        final_bytes = out_io.getvalue()

        if len(final_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="图片处理后仍超过 300KB，拒绝上传")

    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=400, detail="图片处理失败")

    safe_filename = f"{uuid.uuid4().hex}.jpg"
    real_url = await upload_to_beeimg(final_bytes, safe_filename)

    return {"code": 0, "data": {"url": real_url}, "message": "上传成功"}


@router.post("/verify")
async def upload_verify_doc(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    if not ENABLE_VERIFY_UPLOAD:
        raise HTTPException(status_code=403, detail="Demo 测试环境，禁止上传真实证件！请使用仅供测试假材料。")

    contents = await file.read()
    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="文件不能超过 2MB")

    kind = filetype.guess(contents)
    if not kind or kind.mime not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/PDF 格式")

    ext = ".jpg" if kind.mime == "image/jpeg" else (".png" if kind.mime == "image/png" else ".pdf")
    safe_filename = f"{uuid.uuid4().hex}{ext}"

    real_url = await upload_to_beeimg(contents, safe_filename)
    return {"code": 0, "data": {"url": real_url}, "message": "证件上传成功"}