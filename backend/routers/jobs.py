# backend/routers/jobs.py (岗位业务接口：全量完整版，包含流水与幂等)
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timedelta
from database import get_db
# 🚨 核心修复：补上了 PointTransaction 的导入
from models import Job, JobApplication, User, CooperationEntity, Notification, Review, Interview, ApplicationLog, \
    PointTransaction, City, JobPromotion
from core.security import get_current_user, get_optional_user, require_roles, apply_city_filter, verify_resource_city
from services.risk_rules import evaluate_job
from services.promotion import award_promotion
import json
import os

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# 加热置顶：每天消耗的企业推广积分
BOOST_POINTS_PER_DAY = int(os.environ.get("BOOST_POINTS_PER_DAY", "30"))


class JobCreateReq(BaseModel):
    title: str
    salary: str
    location: str
    job_type: str = "long_term"
    filter_tag: str = ""
    tags: str = "日结"
    description: Optional[str] = ""
    requirement: Optional[str] = ""
    cover_image: Optional[str] = ""
    # 本岗位每成功推广一单奖励的积分（B 端发布时设定）
    promotion_points: int = 0


class ReviewReq(BaseModel):
    application_id: int
    rating: int
    comment: str = ""


class InviteReq(BaseModel):
    application_id: int
    time: str
    address: str
    method: Optional[str] = "线下"


class ApplyReq(BaseModel):
    resume_id: Optional[str] = None


# ==========================================
# 第一部分：静态路径
# ==========================================

@router.get("/list")
async def get_jobs(
        job_type: Optional[str] = None,
        filter_tag: Optional[str] = None,
        keyword: Optional[str] = None,
        city_id: Optional[str] = None,
        district: Optional[str] = None,
        x_city_id: Optional[str] = Header(None),
        page: int = 1,
        size: int = 10,
        db: AsyncSession = Depends(get_db),
        current_user: User | None = Depends(get_optional_user)
):
    # 🚨 城市白名单改为查 cities 表（新增城市只需插数据，不再改代码）
    active_cities = (await db.execute(
        select(City.id).where(City.status == "active"))).scalars().all()
    if not active_cities:
        raise HTTPException(status_code=503, detail="城市字典未初始化")

    current_city = x_city_id or city_id or active_cities[0]
    if current_city not in active_cities:
        raise HTTPException(status_code=400, detail="当前城市暂未开放")

    query = select(Job, CooperationEntity.name).join(
        CooperationEntity, Job.merchant_id == CooperationEntity.user_id).where(
        CooperationEntity.status == "active", Job.publish_status == "active")

    query = query.where(Job.city_id == current_city)
    if current_user and current_user.role in ["merchant", "provider", "city_ops", "city_gov", "city_admin"]:
        query = query.where(Job.city_id == current_user.city_id)

    if job_type: query = query.where(Job.job_type == job_type)
    if filter_tag: query = query.where(Job.filter_tag == filter_tag)
    if keyword: query = query.where(Job.title.contains(keyword))
    # 「附近」：按企业注册地所在区/镇大范围筛选
    if district: query = query.where(Job.district.contains(district))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    # 加热置顶的岗位排在前面（pinned_until > now），其余按发布时间倒序
    query = query.order_by(
        Job.pinned_until.is_(None),
        Job.pinned_until.desc(),
        func.coalesce(Job.refreshed_at, Job.created_at).desc(),
        Job.id.desc(),
    )
    result = await db.execute(query.offset((page - 1) * size).limit(size))

    data = []
    for job, company_name in result.all():
        data.append({
            "id": job.id, "title": job.title, "salary": job.salary, "location": job.location,
            "job_type": job.job_type, "tags": job.tags, "filter_tag": job.filter_tag,
            "company_name": company_name or "",
            "cover_image": job.cover_image or "",
            "district": job.district or "",
            "description": (job.description or "")[:60],
            "pinned_until": job.pinned_until.strftime("%Y-%m-%d %H:%M") if job.pinned_until else "",
            "created_at": job.created_at
        })
    return {"code": 0, "data": data, "total": total}


@router.get("/my-list")
async def get_my_jobs(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["merchant", "provider", "hq_ops"]))
):
    m_res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == current_user.id))
    entity = m_res.scalar_one_or_none()
    is_verified = (entity.status == "active") if entity else False
    result = await db.execute(select(Job).where(Job.merchant_id == current_user.id).order_by(Job.id.desc()))
    return {"code": 0, "is_verified": is_verified, "data": result.scalars().all()}


@router.get("/received-count")
async def get_received_count(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["merchant", "provider"]))
):
    query = select(func.count(JobApplication.id)).join(Job, JobApplication.job_id == Job.id).where(
        Job.merchant_id == current_user.id, JobApplication.status == 1)
    count = (await db.execute(query)).scalar()
    return {"code": 0, "data": {"count": count}}


@router.get("/interview-count")
async def get_interview_count(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["merchant", "provider"]))
):
    query = select(func.count(JobApplication.id)).join(Job, JobApplication.job_id == Job.id).where(
        Job.merchant_id == current_user.id, JobApplication.status.in_([2, 3]))
    count = (await db.execute(query)).scalar()
    return {"code": 0, "data": {"count": count}}


@router.get("/my-applications")
async def get_my_applications(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["worker", "hq_ops"]))
):
    query = select(
        JobApplication, Job.id, Job.title, Job.salary, Job.location,
        Interview.interview_time, Interview.interview_address
    ).join(Job, JobApplication.job_id == Job.id).outerjoin(
        Interview, (Interview.job_id == JobApplication.job_id) & (Interview.worker_id == JobApplication.worker_id)
    ).where(
        JobApplication.worker_id == current_user.id
    ).order_by(JobApplication.id.desc())

    result = await db.execute(query)
    data = []
    for app, job_id, title, salary, location, int_time, int_addr in result.all():
        status_map = {1: "待处理", 2: "待面试", 3: "面试已同意", 4: "面试已拒绝", 5: "已录用", 6: "不合适",
                      7: "申请结单中", 8: "已完工", 9: "结单争议", 10: "已失效"}
        data.append({
            "id": app.id, "job_id": job_id, "title": title, "salary": salary, "location": location,
            "status": status_map.get(app.status),
            # 数值状态，前端进度条用（字符串状态只用于展示）
            "status_code": app.status, "reject_reason": app.reject_reason,
            "settled_points": app.settled_points,
            "interview_time": int_time,
            "interview_address": int_addr,
            "created_at": app.created_at.strftime("%m-%d %H:%M") if app.created_at else "",
            "invite_time": app.invite_time.strftime("%m-%d %H:%M") if app.invite_time else "",
            "interview_confirm_time": app.interview_confirm_time.strftime(
                "%m-%d %H:%M") if app.interview_confirm_time else "",
            "hired_time": app.hired_time.strftime("%m-%d %H:%M") if app.hired_time else "",
            "finish_time": app.finish_time.strftime("%m-%d %H:%M") if app.finish_time else ""
        })
    return {"code": 0, "data": data}


@router.get("/received")
async def get_received(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["merchant", "provider"]))
):
    query = select(
        JobApplication, Job.title, Job.salary, Job.location,
        User.phone, User.nickname, User.resume_data
    ).join(Job, JobApplication.job_id == Job.id).join(
        User, JobApplication.worker_id == User.id
    ).where(Job.merchant_id == current_user.id).order_by(JobApplication.id.desc())

    result = await db.execute(query)
    data = []
    for app, title, salary, location, phone, nickname, resume_data in result.all():
        data.append({
            "id": app.id, "job_title": title, "salary": salary, "location": location,
            "worker_name": nickname, "worker_phone": phone, "status": app.status,
            "resume_data": resume_data or {},
            "created_at": app.created_at.strftime("%m-%d %H:%M") if app.created_at else "",
            "invite_time": app.invite_time.strftime("%m-%d %H:%M") if app.invite_time else "",
            "interview_confirm_time": app.interview_confirm_time.strftime(
                "%m-%d %H:%M") if app.interview_confirm_time else "",
            "hired_time": app.hired_time.strftime("%m-%d %H:%M") if app.hired_time else "",
            "finish_time": app.finish_time.strftime("%m-%d %H:%M") if app.finish_time else ""
        })
    return {"code": 0, "data": data}


@router.get("/pending-reviews")
async def get_pending_reviews(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["merchant", "provider"]))
):
    query = select(JobApplication, Job.title, User.nickname).join(Job, JobApplication.job_id == Job.id).join(User,
                                                                                                             JobApplication.worker_id == User.id).outerjoin(
        Review, Review.application_id == JobApplication.id).where(
        Job.merchant_id == current_user.id, JobApplication.status == 8, Review.id == None
    ).order_by(JobApplication.id.desc())
    result = await db.execute(query)
    data = []
    for app, title, nickname in result.all():
        data.append({"application_id": app.id, "worker_name": nickname, "job_title": title,
                     "finish_time": app.finish_time.strftime("%m-%d %H:%M") if app.finish_time else "未知"})
    return {"code": 0, "data": data}


@router.post("/create")
async def create_job(req: JobCreateReq, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(require_roles(
                         ["merchant", "provider"],
                         deny_message="当前账号为求职者身份，请先完成商家认证后再发布岗位"))):
    res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == current_user.id))
    entity = res.scalar_one_or_none()
    initial_status = "active" if (entity and entity.status == "active") else "draft"

    # 🚨 风控第一层：确定性规则（敏感词 / 联系方式 / 薪资异常 / 行业不匹配）
    industry = ""
    entity_name = ""
    entity_district = ""
    if entity:
        entity_name = entity.name or ""
        if entity.ext_info:
            industry = entity.ext_info.get("industry", "") or ""
            entity_district = entity.ext_info.get("district", "") or ""

    risk = evaluate_job(req.title, req.description, req.requirement, req.salary, industry, entity_name)

    # 推广积分：0~200，未设则 0（不参与推广结算）
    promo_points = max(0, min(int(req.promotion_points or 0), 200))

    # 命中拦截线：强制回到草稿，不允许直接上架
    if risk.decision == "blocked":
        initial_status = "draft"

    job = Job(merchant_id=current_user.id, title=req.title, salary=req.salary, location=req.location,
              job_type=req.job_type,
              filter_tag=req.filter_tag, tags=req.tags, description=req.description, requirement=req.requirement,
              publish_status=initial_status, city_id=current_user.city_id,
              cover_image=(req.cover_image or ""), district=entity_district,
              promotion_points=promo_points,
              risk_score=int(round(risk.score * 100)),
              risk_points=json.dumps(risk.to_dict(), ensure_ascii=False),
              risk_status=risk.decision,
              risk_checked_at=datetime.utcnow())
    db.add(job)
    await db.commit()

    if risk.decision == "blocked":
        message = f"岗位触发风控拦截，已保存为草稿：{risk.as_text()}"
    elif risk.decision == "review":
        message = f"岗位已提交，待平台人工复核：{risk.as_text()}"
    else:
        message = "发布成功"

    return {"code": 0, "message": message, "status": initial_status,
            "promotion_points": promo_points, "risk": risk.to_dict()}


# ==========================================
# 第二部分：动态路由
# ==========================================

@router.post("/apply/{job_id:int}")
async def apply_job(
        job_id: int,
        req: ApplyReq = None,
        promoter: Optional[int] = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["worker"]))
):
    try:
        # 🚨 首次接单前置：必须完成实名 + 人脸核验
        if current_user.verify_status != "verified":
            raise HTTPException(status_code=403, detail="请先完成实名认证（含人脸核验）后再投递")

        # 🚨 岗位有效性校验：原实现可对不存在/已下架/草稿岗位投递
        job = await db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="岗位不存在")
        if job.publish_status != "active":
            raise HTTPException(status_code=400, detail="该岗位当前不可投递")

        exist = await db.execute(
            select(JobApplication).where(JobApplication.job_id == job_id, JobApplication.worker_id == current_user.id))
        if exist.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="您已投递过该岗位，请勿重复投递")

        # 🚨 推广归属：只有确实推广过该岗位的人才记，防止链接参数被伪造
        promoter_id = None
        if promoter and promoter != current_user.id:
            promoted = (await db.execute(
                select(JobPromotion).where(
                    JobPromotion.job_id == job_id,
                    JobPromotion.promoter_id == promoter))).scalar_one_or_none()
            if promoted:
                promoter_id = promoter

        new_app = JobApplication(
            job_id=job_id, worker_id=current_user.id,
            city_id=current_user.city_id, promoter_id=promoter_id)
        db.add(new_app)
        await db.flush()

        resume_info = f"，使用简历: {req.resume_id}" if req and req.resume_id else ""
        db.add(ApplicationLog(application_id=new_app.id, operator_type="worker", action="投递简历", detail=resume_info))
        await db.commit()
        return {"code": 0, "message": "投递成功"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        print(f"🚨 投递接口崩溃报错: {str(e)}")
        if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="您已投递过该岗位，请勿重复投递")
        raise HTTPException(status_code=500, detail="平台服务器开小差了，请稍后重试")


@router.get("/{job_id:int}")
async def get_job_detail(
        job_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User | None = Depends(get_optional_user)
):
    job = await db.get(Job, job_id)
    if not job: raise HTTPException(status_code=404, detail="岗位不存在")

    verify_resource_city(job.city_id, current_user)

    merchant = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == job.merchant_id))
    entity = merchant.scalar_one_or_none()
    ext_info = entity.ext_info if (entity and entity.ext_info) else {}

    return {
        "code": 0,
        "data": {
            "job": {
                "id": job.id, "title": job.title, "salary": job.salary,
                "location": job.location, "description": job.description,
                "requirement": job.requirement, "tags": job.tags,
                "cover_image": job.cover_image or "",
                "district": job.district or "",
                "filter_tag": job.filter_tag or "",
                "job_type": job.job_type,
                "created_at": job.created_at.strftime("%Y-%m-%d") if job.created_at else ""
            },
            "company": {
                "company_name": entity.name if entity else "未知",
                "intro": ext_info.get("intro", "暂无简介"),
                "industry": ext_info.get("industry", ""),
                "district": ext_info.get("district", ""),
                "address": ext_info.get("address_detail", ""),
                "cover_image": ext_info.get("cover_image", "")
            }
        }
    }


@router.put("/{job_id:int}/publish")
async def publish_draft_job(job_id: int, db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(require_roles(
                                ["merchant", "provider"],
                                deny_message="当前账号为求职者身份，请先完成商家认证后再上架岗位"))):
    ent_res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == current_user.id))
    entity = ent_res.scalar_one_or_none()
    if not entity or entity.status != "active": raise HTTPException(status_code=403, detail="企业未认证")
    job = await db.get(Job, job_id)
    if not job or job.merchant_id != current_user.id: raise HTTPException(status_code=404, detail="岗位不存在")

    verify_resource_city(job.city_id, current_user)

    # 🚨 风控闸门：创建时已判定；被拦截的岗位必须等平台人工复核放行（risk_status=pass）才能上架。
    # 当前没有岗位编辑接口，内容只可能在创建时写入，因此这里以落库判定为准，无需重复评估。
    if job.risk_status == "blocked":
        raise HTTPException(
            status_code=400,
            detail=f"该岗位已被风控拦截，需平台复核后才能上架：{job.risk_points}"
        )

    job.publish_status = "active"
    await db.commit()
    return {"code": 0, "message": "岗位已成功上架", "risk_status": job.risk_status}


@router.post("/{job_id:int}/promote")
async def promote_job(job_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """「立即推广」：把岗位分享出去帮平台招工

    任何已登录用户都可推广（B 端服务商、C 端求职者都行），
    同一推广人对同一岗位只记一次；结单后按 PROMOTION_REWARD_POINTS 发积分。
    """
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.publish_status != "active":
        raise HTTPException(status_code=400, detail="该岗位未上架，暂不可推广")

    verify_resource_city(job.city_id, current_user)

    existed = (await db.execute(
        select(JobPromotion).where(
            JobPromotion.job_id == job_id,
            JobPromotion.promoter_id == current_user.id))).scalar_one_or_none()

    is_new = False
    if not existed:
        db.add(JobPromotion(job_id=job_id, promoter_id=current_user.id, city_id=job.city_id))
        await db.commit()
        is_new = True

    total = (await db.execute(
        select(func.count()).select_from(JobPromotion)
        .where(JobPromotion.job_id == job_id))).scalar()

    return {"code": 0, "message": "推广链接已生成", "data": {
        "job_id": job_id,
        "promoters": total or 0,
        "is_new": is_new,
        "link": f"/#/worker/job-detail/{job_id}?promoter={current_user.id}",
    }}


@router.put("/{job_id:int}/offline")
async def offline_job(job_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(require_roles(
                          ["merchant", "provider"],
                          deny_message="当前账号为求职者身份，请先完成商家认证"))):
    """下架停招：publish_status -> stopped（不删除数据，可重新上架）"""
    job = await db.get(Job, job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.publish_status != "active":
        raise HTTPException(status_code=400, detail="只有已上架的岗位可以下架")

    job.publish_status = "stopped"
    await db.commit()
    return {"code": 0, "message": "岗位已下架停招"}


@router.put("/{job_id:int}/refresh")
async def refresh_job(job_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(require_roles(
                          ["merchant", "provider"],
                          deny_message="当前账号为求职者身份，请先完成商家认证"))):
    """刷新岗位：更新 refreshed_at，C 端列表排序靠前"""
    job = await db.get(Job, job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.publish_status != "active":
        raise HTTPException(status_code=400, detail="只有已上架的岗位可以刷新")

    job.refreshed_at = datetime.utcnow()
    await db.commit()
    return {"code": 0, "message": "刷新成功，岗位排序已提升"}


@router.delete("/{job_id:int}")
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(require_roles(
                         ["merchant", "provider"],
                         deny_message="当前账号为求职者身份，请先完成商家认证"))):
    """删除岗位：仅草稿且无人投递时允许"""
    job = await db.get(Job, job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.publish_status != "draft":
        raise HTTPException(status_code=400, detail="只有草稿岗位可以删除，已上架的请先下架")

    applied = (await db.execute(
        select(func.count()).select_from(JobApplication)
        .where(JobApplication.job_id == job_id))).scalar() or 0
    if applied > 0:
        raise HTTPException(status_code=400, detail=f"该岗位已有 {applied} 条投递，不能删除")

    await db.delete(job)
    await db.commit()
    return {"code": 0, "message": "岗位已删除"}


@router.post("/{job_id:int}/boost")
async def boost_job(job_id: int, days: int = 7, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(require_roles(
                        ["merchant", "provider"],
                        deny_message="当前账号为求职者身份，请先完成商家认证"))):
    """加热置顶：按天从企业推广余额扣费，C 端列表排到最前"""
    job = await db.get(Job, job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.publish_status != "active":
        raise HTTPException(status_code=400, detail="请先上架岗位后再加热")

    days = max(1, min(int(days or 7), 30))
    cost = BOOST_POINTS_PER_DAY * days

    entity = (await db.execute(
        select(CooperationEntity).where(CooperationEntity.user_id == current_user.id)
    )).scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="企业档案不存在")

    balance = entity.promotion_balance or 0
    if balance < cost:
        raise HTTPException(
            status_code=400,
            detail=f"推广余额不足：需要 {cost} 分，当前 {int(balance)} 分，请联系运营充值",
        )

    entity.promotion_balance = balance - cost

    now = datetime.utcnow()
    base = job.pinned_until if (job.pinned_until and job.pinned_until > now) else now
    job.pinned_until = base + timedelta(days=days)

    db.add(Notification(
        user_id=current_user.id,
        title="岗位已加热置顶",
        content=f"【{job.title}】已置顶 {days} 天，消耗 {cost} 推广积分，"
                f"当前余额 {int(entity.promotion_balance)} 分。",
    ))
    await db.commit()

    return {"code": 0, "message": f"已加热置顶 {days} 天", "data": {
        "pinned_until": job.pinned_until.strftime("%Y-%m-%d %H:%M"),
        "cost": cost,
        "promotion_balance": int(entity.promotion_balance),
    }}


@router.put("/application/{app_id:int}")
async def update_app_status(app_id: int, status: int, reason: str = "", db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(require_roles(["merchant", "provider"]))):
    app = await db.get(JobApplication, app_id)
    if not app: raise HTTPException(status_code=404, detail="不存在")

    # 🚨 归属校验：只能操作自己企业的单据（原实现可跨租户改任意工单）
    job = await db.get(Job, app.job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：无权操作该单据")

    # 🚨 白名单：本接口只负责「录用 / 初筛拒绝」，其余状态走专用接口
    if status not in (5, 6):
        raise HTTPException(status_code=400, detail="该接口仅允许设置 5(录用) 或 6(不合适)")

    # 🚨 终态保护：已完工/争议/失效的单据不可再回流
    if app.status in (8, 9, 10):
        raise HTTPException(status_code=400, detail="单据已结束，不可再变更状态")

    app.status = status
    if status == 5:
        app.hired_time = datetime.utcnow()
        db.add(ApplicationLog(application_id=app.id, operator_type="merchant", action="确认录用"))
    if status == 6 and reason:
        app.reject_reason = reason
        db.add(ApplicationLog(application_id=app.id, operator_type="merchant", action="初筛拒绝", detail=reason))
    await db.commit()
    return {"code": 0, "message": "操作成功"}


@router.put("/application/{app_id:int}/finish")
async def apply_finish(app_id: int, photo_url: str = "", db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(require_roles(["worker"]))):
    app = await db.get(JobApplication, app_id)
    if not app or app.worker_id != current_user.id: raise HTTPException(status_code=404, detail="记录不存在")

    # 🚨 状态前置：必须已被录用(5)才能申请完工，防止投递后直接跳结单
    if app.status != 5:
        raise HTTPException(status_code=400, detail="当前状态不可申请完工（需先被录用）")

    app.status = 7
    app.finish_time = datetime.utcnow()
    app.evidence_photo = photo_url

    job = await db.get(Job, app.job_id)
    db.add(Notification(user_id=job.merchant_id, title="收到完工结单申请",
                        content=f"求职者申请对【{job.title}】完工，请及时确认。"))
    db.add(ApplicationLog(application_id=app.id, operator_type="worker", action="申请完工", evidence_photo=photo_url))
    await db.commit()
    return {"code": 0, "message": "已提交完工申请"}


@router.put("/application/{app_id:int}/confirm-finish")
async def confirm_finish(app_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(require_roles(["merchant", "provider"]))):
    app = await db.get(JobApplication, app_id)
    if not app: raise HTTPException(status_code=404, detail="记录不存在")

    # 🚨 修复：防止重复确认
    if app.status == 8:
        return {"code": 0, "message": "订单已确认完工"}

    job = await db.get(Job, app.job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：无权操作该单据")
    if app.status != 7:
        raise HTTPException(status_code=400, detail="单据当前状态不可确认")

    reward_points = 50
    app.status = 8
    app.settled_points = reward_points
    worker = await db.get(User, app.worker_id)
    worker.total_points += reward_points

    # 🚨 修复：写入积分流水（补 city_id，否则跨城对账失真）
    db.add(PointTransaction(
        user_id=worker.id, city_id=job.city_id, amount=reward_points,
        balance_after=worker.total_points,
        biz_type="order_settle", ref_no=f"settle_{app.id}", order_id=str(app.id),
        remark=f"订单【{job.title}】完工结算"
    ))

    # 🚨 推广奖励：结单时给推广人发积分（一单一次）
    await award_promotion(db, app, job)

    db.add(Notification(user_id=app.worker_id, title="完工结单已确认",
                        content=f"企业已确认完工，{reward_points}积分已到账！"))
    db.add(ApplicationLog(application_id=app.id, operator_type="merchant", action="确认完工",
                          detail=f"发放{reward_points}积分"))
    await db.commit()
    return {"code": 0, "message": "已确认完工并发放积分"}


@router.put("/application/{app_id:int}/reject-finish")
async def reject_finish(app_id: int, reason: str, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(require_roles(["merchant", "provider"]))):
    app = await db.get(JobApplication, app_id)
    if not app: raise HTTPException(status_code=404, detail="记录不存在")
    job = await db.get(Job, app.job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：无权操作该单据")
    if app.status != 7:
        raise HTTPException(status_code=400, detail="单据当前状态不可驳回")
    app.status = 9
    db.add(
        Notification(user_id=app.worker_id, title="结单申请被驳回", content=f"企业拒绝了您的结单申请，原因：{reason}。"))
    db.add(ApplicationLog(application_id=app.id, operator_type="merchant", action="驳回结单", detail=reason))
    await db.commit()
    return {"code": 0, "message": "已驳回结单申请"}


@router.post("/review")
async def submit_review(req: ReviewReq, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(require_roles(["merchant", "provider"]))):
    app = await db.get(JobApplication, req.application_id)
    if not app: raise HTTPException(status_code=404, detail="记录不存在")

    # 🚨 归属校验：原实现可对任意企业的单据提交评价
    job = await db.get(Job, app.job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：无权评价该单据")

    # 🚨 只有已完工的单据可评价
    if app.status != 8:
        raise HTTPException(status_code=400, detail="单据尚未完工，暂不可评价")

    # 🚨 修复：防止重复评价
    exist_review = await db.execute(select(Review).where(Review.application_id == req.application_id))
    if exist_review.scalar_one_or_none():
        return {"code": 0, "message": "已评价过"}

    db.add(Review(application_id=req.application_id, merchant_id=current_user.id, worker_id=app.worker_id,
                  rating=req.rating, comment=req.comment))
    await db.commit()
    return {"code": 0, "message": "评价提交成功"}


@router.post("/interview/invite")
async def invite_interview(req: InviteReq, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(require_roles(["merchant", "provider"]))):
    app = await db.get(JobApplication, req.application_id)
    if not app: raise HTTPException(status_code=404, detail="记录不存在")

    # 🚨 归属校验：原实现可对任意企业的投递发起面试邀请
    job = await db.get(Job, app.job_id)
    if not job or job.merchant_id != current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：无权操作该单据")

    # 🚨 状态前置：只有待处理/待面试的投递可以邀面试
    if app.status not in (1, 2):
        raise HTTPException(status_code=400, detail="当前状态不可发起面试邀请")

    app.status = 2
    app.invite_time = datetime.utcnow()

    db.add(Interview(job_id=app.job_id, merchant_id=current_user.id, worker_id=app.worker_id, interview_time=req.time,
                     interview_address=req.address, method=req.method))
    db.add(Notification(user_id=app.worker_id, title="收到面试邀请",
                        content=f"企业邀请您参加面试。时间：{req.time}，地点：{req.address}。"))
    db.add(ApplicationLog(application_id=app.id, operator_type="merchant", action="邀面试",
                          detail=f"时间：{req.time}，地点：{req.address}"))
    await db.commit()
    return {"code": 0, "message": "面试邀请已发送"}


@router.put("/interview/{app_id:int}/reply")
async def reply_interview(app_id: int, accept: bool, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(require_roles(["worker"]))):
    app = await db.get(JobApplication, app_id)
    if not app or app.worker_id != current_user.id: raise HTTPException(status_code=404, detail="记录不存在")
    app.status = 3 if accept else 4
    app.interview_confirm_time = datetime.utcnow()

    action_text = "同意面试" if accept else "拒绝面试"
    db.add(ApplicationLog(application_id=app.id, operator_type="worker", action=action_text))
    await db.commit()
    return {"code": 0, "message": "回复成功"}


@router.get("/timeline/{app_id:int}")
async def get_timeline(app_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    app = await db.get(JobApplication, app_id)
    if not app: raise HTTPException(status_code=404, detail="记录不存在")
    job = await db.get(Job, app.job_id)

    is_merchant = (job.merchant_id == current_user.id)
    is_worker = (app.worker_id == current_user.id)
    if not (is_merchant or is_worker) and not current_user.role.startswith("hq_"):
        raise HTTPException(status_code=403, detail="无权查看该订单记录")

    query = select(ApplicationLog).where(ApplicationLog.application_id == app_id).order_by(ApplicationLog.id.asc())
    result = await db.execute(query)
    return {"code": 0, "data": result.scalars().all()}