"""图形验证码（登录前置）

设计
----
· 只依赖标准库，生成 SVG 字符验证码，不引入 Pillow 渲染与字体依赖。
· 答案存 Redis（生产）或进程内字典（本地/Redis 不可用时的降级），一次性消费。
· 开关 `ENABLE_CAPTCHA`（默认 false）：测试阶段不强制，接入短信/风控后置 true。

使用方式
--------
    GET  /api/auth/captcha            -> { captcha_id, svg }
    POST /api/auth/login { ..., captcha_id, captcha_code }

接入真实短信验证码时，同一套 store 可复用为短信码存储。
"""
import os
import random
import string
import time
import uuid

from database import redis_client

CAPTCHA_TTL_SECONDS = int(os.environ.get("CAPTCHA_TTL_SECONDS", "180"))
CAPTCHA_LENGTH = int(os.environ.get("CAPTCHA_LENGTH", "4"))

# Redis 不可用时的进程内降级存储：{captcha_id: (answer, expire_ts)}
_memory_store = {}


def _cleanup_memory() -> None:
    now = time.time()
    for key in [k for k, (_, exp) in _memory_store.items() if exp < now]:
        _memory_store.pop(key, None)


def _random_code() -> str:
    # 去掉易混淆字符（0/O/1/I/L）
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(CAPTCHA_LENGTH))


def _render_svg(code: str) -> str:
    """把验证码渲染成 SVG：每个字符带轻微旋转与随机色"""
    width, height = 120, 44
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" rx="8" fill="#f2f6fc"/>',
    ]

    # 干扰线
    for _ in range(3):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#c9d8ee" stroke-width="1"/>'
        )

    step = width // (CAPTCHA_LENGTH + 1)
    colors = ["#1677ff", "#1f4f8f", "#ff7a1a", "#0f9d58", "#7a4dff"]
    for i, ch in enumerate(code):
        x = step * (i + 1)
        y = height // 2 + random.randint(-3, 3)
        rotate = random.randint(-18, 18)
        color = random.choice(colors)
        parts.append(
            f'<text x="{x}" y="{y}" font-size="24" font-weight="700" '
            f'font-family="Menlo,Consolas,monospace" fill="{color}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'transform="rotate({rotate} {x} {y})">{ch}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


async def create_captcha() -> dict:
    """生成验证码并落库，返回 id 与 SVG"""
    code = _random_code()
    captcha_id = uuid.uuid4().hex
    expire_at = time.time() + CAPTCHA_TTL_SECONDS

    if redis_client is not None:
        try:
            await redis_client.set(f"captcha:{captcha_id}", code, ex=CAPTCHA_TTL_SECONDS)
            return {"captcha_id": captcha_id, "svg": _render_svg(code),
                    "expire_in": CAPTCHA_TTL_SECONDS}
        except Exception:
            pass  # Redis 抖动时降级到内存

    _cleanup_memory()
    _memory_store[captcha_id] = (code, expire_at)
    return {"captcha_id": captcha_id, "svg": _render_svg(code), "expire_in": CAPTCHA_TTL_SECONDS}


async def verify_captcha(captcha_id: str, captcha_code: str) -> bool:
    """一次性校验：无论成功失败都销毁"""
    if not captcha_id or not captcha_code:
        return False

    expected = None
    if redis_client is not None:
        try:
            expected = await redis_client.get(f"captcha:{captcha_id}")
            if expected:
                await redis_client.delete(f"captcha:{captcha_id}")
        except Exception:
            expected = None

    if expected is None:
        item = _memory_store.pop(captcha_id, None)
        if item and item[1] > time.time():
            expected = item[0]

    if not expected:
        return False
    return str(expected).strip().upper() == str(captcha_code).strip().upper()


def captcha_enabled() -> bool:
    return os.environ.get("ENABLE_CAPTCHA", "false").strip().lower() in ("1", "true", "yes", "on")
