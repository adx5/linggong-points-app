"""推广奖励结算（B 端预付，平台不代收 C 端资金 → 规避二清）

归属链路：
  推广人分享岗位（链接带 ?promoter=xx）
    → 求职者投递时带上 promoter，校验确实推广过该岗位后落到 job_applications.promoter_id
    → 工单结单（商家确认完工 / 系统超时自动结单）

计费链路：
  B 端先充值「推广积分余额」（线下对公转账 + 后台记账）
    → 发布岗位时设定该岗位「每单推广积分」（日结/长期可不同）
    → 结单时从企业余额扣 N 分，给推广人发 N 分
    → 余额不足则不发放，并通知企业补足
"""
import os

from sqlalchemy import select

from models import CooperationEntity, Notification, PointTransaction, User

# 建议默认值（实际以岗位发布时设定的 promotion_points 为准），仅用于前端展示
PROMOTION_REWARD_POINTS = int(os.environ.get("PROMOTION_REWARD_POINTS", "20"))


async def award_promotion(db, application, job) -> int:
    """结单时按岗位设定的推广积分结算；返回实际发放积分数（0 表示未发放）

    只做 db.add / 属性修改，不 commit —— 与工单结单放在同一事务里。
    """
    points = int(getattr(job, "promotion_points", 0) or 0)
    if points <= 0:
        return 0

    promoter_id = getattr(application, "promoter_id", None)
    if not promoter_id or promoter_id == application.worker_id:
        return 0

    promoter = await db.get(User, promoter_id)
    if not promoter:
        return 0

    entity = (await db.execute(
        select(CooperationEntity).where(CooperationEntity.user_id == job.merchant_id)
    )).scalar_one_or_none()

    if not entity or (entity.promotion_balance or 0) < points:
        # 企业推广余额不足：不发奖励，通知企业补足
        db.add(Notification(
            user_id=job.merchant_id,
            title="推广余额不足",
            content=f"岗位【{job.title}】产生一笔推广结算（{points} 分），但您的推广余额不足，"
                    f"本次未发放，请及时充值后补偿。",
        ))
        return 0

    entity.promotion_balance = (entity.promotion_balance or 0) - points

    balance = (promoter.total_points or 0) + points
    promoter.total_points = balance

    db.add(PointTransaction(
        user_id=promoter_id,
        city_id=job.city_id,
        amount=points,
        balance_after=balance,
        biz_type="promotion_reward",
        ref_no=f"promo_{application.id}",
        order_id=str(application.id),
        remark=f"推广岗位【{job.title}】结单奖励",
    ))
    db.add(Notification(
        user_id=promoter_id,
        title="推广奖励到账",
        content=f"您推广的岗位【{job.title}】已完成结单，{points} 积分已到账。",
    ))
    return points
