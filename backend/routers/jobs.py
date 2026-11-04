# backend/routers/jobs.py (岗位业务接口：全量完整版，包含带出面试时间地点)
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
from database import get_db
from models import Job, JobApplication, User, CooperationEntity, Notification, Review, Interview, ApplicationLog
from core.security import get_current_user, get_optional_user, require_roles, apply_city_filter, verify_resource_city

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobCreateReq(BaseModel):
    title: str
    salary: str
    location: str
    job_type: str = "long_term"
    filter_tag: str = ""
    tags: str = "日结"
    description: Optional[str] = ""
    requirement: Optional[str] = ""


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
        x_city_id: Optional[str] = Header(None),
        page: int = 1,
        size: int = 10,
        db: AsyncSession = Depends(get_db),
        current_user: User | None = Depends(get_optional_user)
):
    current_city = x_city_id or city_id or "410185"

    if current_city not in ['410185', '410173', '411300']:
        raise HTTPException(status_code=400, detail="当前城市暂未开放")

    query = select(Job).join(CooperationEntity, Job.merchant_id == CooperationEntity.user_id).where(
        CooperationEntity.status == "active", Job.publish_status == "active")

    query = query.where(Job.city_id == current_city)

    if current_user and current_user.role in ["merchant", "provider", "city_ops", "city_gov", "city_admin"]:
        query = query.where(Job.city_id == current_user.city_id)

    if job_type: query = query.where(Job.job_type == job_type)
    if filter_tag: query = query.where(Job.filter_tag == filter_tag)
    if keyword: query = query.where(Job.title.contains(keyword))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.order_by(Job.id.desc()).offset((page - 1) * size).limit(size))

    data = []
    for job in result.scalars().all():
        data.append({
            "id": job.id, "title": job.title, "salary": job.salary, "location": job.location,
            "job_type": job.job_type, "tags": job.tags, "created_at": job.created_at
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


# 🚨 修复：联表带出面试时间和地点
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
            "status": status_map.get(app.status), "reject_reason": app.reject_reason,
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
                     current_user: User = Depends(require_roles(["merchant", "provider"]))):
    res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == current_user.id))
    entity = res.scalar_one_or_none()
    initial_status = "active" if (entity and entity.status == "active") else "draft"
    job = Job(merchant_id=current_user.id, title=req.title, salary=req.salary, location=req.location,
              job_type=req.job_type,
              filter_tag=req.filter_tag, tags=req.tags, description=req.description, requirement=req.requirement,
              publish_status=initial_status, city_id=current_user.city_id)
    db.add(job)
    await db.commit()
    return {"code": 0, "message": "发布成功", "status": initial_status}


# ==========================================
# 第二部分：动态路由
# ==========================================

@router.post("/apply/{job_id:int}")
async def apply_job(
        job_id: int,
        req: ApplyReq = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["worker"]))
):
    try:
        exist = await db.execute(
            select(JobApplication).where(JobApplication.job_id == job_id, JobApplication.worker_id == current_user.id))
        if exist.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="您已投递过该岗位，请勿重复投递")

        new_app = JobApplication(job_id=job_id, worker_id=current_user.id, city_id=current_user.city_id)
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
                "requirement": job.requirement, "tags": job.tags
            },
            "company": {
                "company_name": entity.name if entity else "未知",
                "intro": ext_info.get("intro", "暂无简介")
            }
        }
    }


@router.put("/{job_id:int}/publish")
async def publish_draft_job(job_id: int, db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(require_roles(["merchant", "provider"]))):
    ent_res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == current_user.id))
    entity = ent_res.scalar_one_or_none()
    if not entity or entity.status != "active": raise HTTPException(status_code=403, detail="企业未认证")
    job = await db.get(Job, job_id)
    if not job or job.merchant_id != current_user.id: raise HTTPException(status_code=404, detail="岗位不存在")

    verify_resource_city(job.city_id, current_user)
    job.publish_status = "active"
    await db.commit()
    return {"code": 0, "message": "岗位已成功上架"}


@router.put("/application/{app_id:int}")
async def update_app_status(app_id: int, status: int, reason: str = "", db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(require_roles(["merchant", "provider"]))):
    app = await db.get(JobApplication, app_id)
    if not app: raise HTTPException(status_code=404, detail="不存在")
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
    db.add(Review(application_id=req.application_id, merchant_id=current_user.id, worker_id=app.worker_id,
                  rating=req.rating, comment=req.comment))
    await db.commit()
    return {"code": 0, "message": "评价提交成功"}


@router.post("/interview/invite")
async def invite_interview(req: InviteReq, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(require_roles(["merchant", "provider"]))):
    app = await db.get(JobApplication, req.application_id)
    if not app: raise HTTPException(status_code=404, detail="记录不存在")
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