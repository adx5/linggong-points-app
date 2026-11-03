# backend/scheduler.py (APScheduler 定时任务：带 Redis 分布式锁、积分流水、绝对幂等)
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from database import AsyncSessionLocal, redis_client
from models import JobApplication, ApplicationLog, Notification, User, Job, PointTransaction

scheduler = AsyncIOScheduler()


async def auto_finish_jobs():
    # 🚨 修复硬伤 5：Redis 不可用直接报警，不静默
    if not redis_client:
        print("🚨 [ALERT] 定时任务严重警告: Redis 未配置，无法执行分布式锁，任务中止。")
        return

    # 🚨 修复硬伤 4：72 小时不写死，读取环境变量，如果未配置（默认0）则不执行
    timeout_hours_str = os.environ.get("AUTO_FINISH_HOURS", "0")
    if timeout_hours_str == "0":
        return
    timeout_hours = int(timeout_hours_str)

    lock_key = "scheduler:auto_finish_jobs"
    try:
        is_locked = await redis_client.set(lock_key, "1", ex=60, nx=True)
        if not is_locked:
            return
    except Exception as e:
        print(f"🚨 [ALERT] 定时任务 Redis 锁异常: {e}")
        return

    try:
        async with AsyncSessionLocal() as db:
            timeout_time = datetime.utcnow() - timedelta(hours=timeout_hours)

            query = select(JobApplication).where(
                JobApplication.status == 7,
                JobApplication.updated_at <= timeout_time
            )
            result = await db.execute(query)
            expired_apps = result.scalars().all()

            for app in expired_apps:
                # 🚨 修复硬伤 3：条件更新，确保在扫描和更新瞬间 B 端没正好点确认
                stmt = update(JobApplication).where(
                    JobApplication.id == app.id,
                    JobApplication.status == 7
                ).values(
                    status=8,
                    settled_points=50,
                    finish_time=datetime.utcnow()
                )

                res = await db.execute(stmt)

                if res.rowcount > 0:
                    # 🚨 修复硬伤 2：补空值兜底
                    worker = await db.get(User, app.worker_id)
                    job = await db.get(Job, app.job_id)

                    if not worker or not job:
                        continue

                    # 🚨 修复硬伤 1：走 PointTransaction 流水
                    reward_points = 50
                    worker.total_points += reward_points

                    ref_no = f"auto_settle:{app.id}"  # 幂等键
                    tx = PointTransaction(
                        user_id=worker.id, city_id=worker.city_id,
                        amount=reward_points, balance_after=worker.total_points,
                        biz_type="auto_settle", ref_no=ref_no,
                        operator_id=0, remark="超时自动结单发放"
                    )
                    db.add(tx)

                    try:
                        await db.flush()
                    except IntegrityError:
                        # 唯一键冲突，说明这笔单已经发过积分了，直接跳过
                        await db.rollback()
                        continue

                    # 🚨 修复硬伤 6：补审计细节、双端通知
                    db.add(ApplicationLog(
                        application_id=app.id, operator_type="system",
                        action="超时自动结单",
                        detail=f"任务ID:auto_finish, 超时阈值:{timeout_hours}h, 原状态:7, 新状态:8, 积分流水号:{ref_no}"
                    ))

                    db.add(Notification(
                        user_id=job.merchant_id, title="系统已自动结单",
                        content=f"岗位【{job.title}】超时未确认，系统已自动完工。"
                    ))
                    db.add(Notification(
                        user_id=worker.id, title="结单完成(系统自动)",
                        content=f"您对【{job.title}】的结单申请已超时自动确认，{reward_points}积分已到账。"
                    ))

            await db.commit()
    except Exception as e:
        print(f"🚨 [ALERT] 定时任务执行异常: {e}")
    finally:
        try:
            await redis_client.delete(lock_key)
        except Exception:
            pass


def start_scheduler():
    # 如果业务配置了生效时间才启动，否则一直挂起
    if os.environ.get("AUTO_FINISH_HOURS", "0") != "0":
        scheduler.add_job(auto_finish_jobs, IntervalTrigger(hours=1))
        scheduler.start()
        print("✅ 超时自动结单定时任务已启动")
    else:
        print("ℹ️ AUTO_FINISH_HOURS 未配置，定时任务不启动")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()