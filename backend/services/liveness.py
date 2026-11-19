"""实名认证 / 人脸活体核验 —— Provider 抽象

接入策略
--------
业务层只依赖 `LivenessProvider.verify()`，切换厂商不改业务代码：

    LIVENESS_PROVIDER=mock      本地/测试（默认，零成本、结果可控）
    LIVENESS_PROVIDER=tencent   腾讯云人脸核身
    LIVENESS_PROVIDER=alipay    支付宝实名核身

腾讯云 / 支付宝两家目前抛错占位，等账号与密钥到位后
实现同名 verify() 并在 get_liveness_provider() 里注册即可。

Mock 的行为约定（便于写测试）
-----------------------------
face_image 里出现以下关键字，走对应分支：
    reject / fail    → rejected        （人脸比对失败）
    manual / blur    → manual_review   （证件模糊，转人工）
    其它             → verified        （通过）
"""
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LivenessResult:
    passed: bool
    status: str                      # verified / rejected / manual_review
    provider: str
    biz_no: str
    liveness_score: float = 0.0
    similarity_score: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class LivenessProvider:
    name = "base"

    async def verify(
            self,
            *,
            user_id: int,
            real_name: str,
            id_card: str,
            face_image: str,
            scene: str = "register",
    ) -> LivenessResult:
        raise NotImplementedError


class MockLivenessProvider(LivenessProvider):
    """测试实现：不调用任何外部服务，结果由 face_image 关键字决定"""

    name = "mock"

    async def verify(self, *, user_id, real_name, id_card, face_image, scene="register") -> LivenessResult:
        biz_no = f"mock-{uuid.uuid4().hex[:16]}"
        marker = (face_image or "").lower()

        if "reject" in marker or "fail" in marker:
            return LivenessResult(
                passed=False, status="rejected", provider=self.name, biz_no=biz_no,
                liveness_score=0.31, similarity_score=0.28,
                raw={"mock": True, "marker": marker, "scene": scene},
                reason="人脸比对失败",
            )

        if "manual" in marker or "blur" in marker:
            return LivenessResult(
                passed=False, status="manual_review", provider=self.name, biz_no=biz_no,
                liveness_score=0.72, similarity_score=0.66,
                raw={"mock": True, "marker": marker, "scene": scene},
                reason="证件模糊或疑似冒用，转人工复核",
            )

        return LivenessResult(
            passed=True, status="verified", provider=self.name, biz_no=biz_no,
            liveness_score=0.98, similarity_score=0.95,
            raw={"mock": True, "marker": marker, "scene": scene},
        )


class TencentLivenessProvider(LivenessProvider):
    name = "tencent"

    async def verify(self, *, user_id, real_name, id_card, face_image, scene="register"):
        raise RuntimeError(
            "腾讯云人脸核身尚未接入：请实现 TencentLivenessProvider.verify()，"
            "并在 .env 配置 TENCENT_SECRET_ID / TENCENT_SECRET_KEY / TENCENT_REGION"
        )


class AlipayLivenessProvider(LivenessProvider):
    name = "alipay"

    async def verify(self, *, user_id, real_name, id_card, face_image, scene="register"):
        raise RuntimeError(
            "支付宝实名核身尚未接入：请实现 AlipayLivenessProvider.verify()，"
            "并在 .env 配置 ALIPAY_APP_ID / ALIPAY_PRIVATE_KEY / ALIPAY_PUBLIC_KEY"
        )


_PROVIDERS = {
    "mock": MockLivenessProvider,
    "tencent": TencentLivenessProvider,
    "alipay": AlipayLivenessProvider,
}


def get_liveness_provider() -> LivenessProvider:
    name = os.environ.get("LIVENESS_PROVIDER", "mock").strip().lower()
    cls = _PROVIDERS.get(name, MockLivenessProvider)
    return cls()


# 允许的认证状态流转（人工兜底审核也走这里）
VERIFY_STATUSES = ("unverified", "pending", "verified", "rejected", "manual_review")
