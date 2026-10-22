"""
schemas.py - Pydantic 请求 / 响应模型
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------- Auth ----------
class PhoneIn(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)


class LoginIn(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    code: str = Field(..., min_length=4, max_length=8)
    referrer_id: Optional[int] = None


class LoginOut(BaseModel):
    user_id: int
    phone: str
    nickname: str
    token: str
    total_points: int
    growth_value: int
    is_new: bool


# ---------- User ----------
class UserProfile(BaseModel):
    id: int
    phone: str
    nickname: str
    growth_value: int
    total_earned: int
    total_spent: int
    total_points: int


class PointsBucketOut(BaseModel):
    id: int
    balance: int
    expire_date: str
    source: str


class LedgerItem(BaseModel):
    id: int
    delta: int
    balance_after: int
    tx_type: str
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    note: Optional[str] = None
    created_at: str


class VerifyItem(BaseModel):
    id: int
    points_spent: int
    growth_delta: int
    is_first_verify: bool
    note: Optional[str] = None
    created_at: str


# ---------- Tasks ----------
class TaskItem(BaseModel):
    id: int
    code: str
    title: str
    description: Optional[str] = None
    reward_points: int
    reward_type: str
    completed: bool


# ---------- Ads ----------
class AdGroupOut(BaseModel):
    id: int
    code: str
    title: str
    description: Optional[str] = None
    points_per_group: int
    callbacks_required: int


class AdCallbackIn(BaseModel):
    ad_group_code: str
    ad_code: str


class AdCallbackOut(BaseModel):
    log_id: int
    group_count: int
    credited: bool
    points_awarded: int


# ---------- Verify ----------
class VerifyCheckIn(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)


class VerifyCheckOut(BaseModel):
    exists: bool
    user_id: Optional[int] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    total_points: Optional[int] = None


class VerifyConsumeIn(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    points: int = Field(..., gt=0)
    note: Optional[str] = None
    store_code: Optional[str] = None


class VerifyConsumeOut(BaseModel):
    verify_id: int
    user_id: int
    points_spent: int
    growth_delta: int
    remaining_points: int
    first_verify: bool
    referrer_rewarded: bool


# ---------- Exchange ----------
class ExchangeItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    points_cost: int
    stock: int


class ExchangeRedeemIn(BaseModel):
    item_id: int


class ExchangeRedeemOut(BaseModel):
    exchange_id: int
    points_spent: int
    remaining_points: int


# ---------- Referral ----------
class ReferralSummaryOut(BaseModel):
    downline_count: int
    total_reward: int


class DownlineItem(BaseModel):
    id: int
    phone: str
    nickname: str
    created_at: str


# ---------- Admin ----------
class AdminLoginIn(BaseModel):
    username: str
    password: str


class AdminLoginOut(BaseModel):
    token: str
    role: str
