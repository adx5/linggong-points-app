"""岗位风险规则引擎 —— 第一层：确定性规则

设计原则
--------
1. **零外部依赖、零误判**：只命中"明确违规 / 明显异常"，不做语义推断。
2. **结果可解释**：每条命中都带分类、命中词、依据文本，人工复核能一眼看懂。
3. **可叠加**：输出 0~1 的 risk_score + 风险标签，第二层 LLM 可在其基础上继续加分。
4. **阈值可配**：
     RISK_BLOCK_THRESHOLD  默认 0.8 —— 达到即自动拦截（岗位回草稿、禁止上架）
     RISK_REVIEW_THRESHOLD 默认 0.5 —— 达到即转人工复核

覆盖的规则
----------
  R1 敏感词命中（色情低俗 / 刷单诈骗 / 违规引流 / 违规收费 / 违法业务）
  R2 联系方式外泄（手机号、微信、QQ）
  R3 薪资异常（月薪远超阈值 / 日结单价离谱）
  R4 岗位与企业经营范围明显不匹配
"""
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

BLOCK_THRESHOLD = float(os.environ.get("RISK_BLOCK_THRESHOLD", "0.8"))
REVIEW_THRESHOLD = float(os.environ.get("RISK_REVIEW_THRESHOLD", "0.5"))

# 月薪异常阈值（元），超过即视为明显异常
SALARY_MONTHLY_MAX = float(os.environ.get("RISK_SALARY_MONTHLY_MAX", "50000"))
# 日结单价异常阈值（元/天）
SALARY_DAILY_MAX = float(os.environ.get("RISK_SALARY_DAILY_MAX", "1500"))

# ==============================================================
# R1 敏感词库（按违规类型分组，便于人工复核时归类处置）
# ==============================================================
SENSITIVE_WORDS: Dict[str, List[str]] = {
    "色情低俗": [
        "陪酒", "陪侍", "三陪", "出台", "包夜", "裸聊", "情色", "夜场公主",
        "商务陪侍", "特殊服务", "特殊按摩", "高薪陪玩",
    ],
    "刷单诈骗": [
        "刷单", "刷信誉", "刷好评", "点赞赚钱", "打字员", "网赚", "躺赚",
        "日入过万", "无需经验高薪", "代练赚钱", "手机兼职日结",
    ],
    "违规引流": [
        "加微信", "加qq", "加QQ", "私聊我", "私信我", "扫码进群",
        "公众号引流", "联系方式见简介", "详情加v",
    ],
    "违规收费": [
        "押金", "保证金", "服装费", "培训费", "介绍费", "体检费",
        "入职费", "办卡费", "押证件",
    ],
    "违法业务": [
        "代开发票", "办证", "信用卡套现", "贷款中介", "博彩", "时时彩",
        "私彩", "传销", "代考", "办假证",
    ],
}

# ==============================================================
# R2 联系方式外泄
# ==============================================================
CONTACT_PATTERNS = [
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "疑似手机号"),
    (re.compile(r"(?i)(微信|weixin|wx|vx|威信)\s*[:：]?\s*[a-zA-Z0-9_-]{5,20}"), "疑似微信号"),
    (re.compile(r"(?i)(qq|扣扣|企鹅)\s*[:：]?\s*\d{5,12}"), "疑似QQ号"),
]

# ==============================================================
# R4 岗位类目 vs 企业行业
# ==============================================================
TITLE_CATEGORY: Dict[str, List[str]] = {
    "娱乐": ["ktv", "夜场", "酒吧", "陪酒", "会所", "足浴", "按摩", "夜店"],
    "餐饮": ["服务员", "厨师", "传菜", "洗碗", "后厨", "餐饮", "面点", "收银"],
    "建筑": ["工地", "钢筋", "水泥", "瓦工", "木工", "装修", "水电工", "架子工"],
    "物流": ["快递", "分拣", "搬运", "货运", "司机", "仓储", "打包"],
    "教育": ["教师", "家教", "助教", "课程顾问", "辅导"],
    "医疗": ["护士", "护理", "医美", "药师", "口腔"],
    "金融": ["贷款", "理财", "保险", "信贷", "催收"],
    "零售": ["五金", "建材", "超市", "便利店", "服装店", "导购", "店长"],
    "制造": ["普工", "操作工", "车间", "装配", "质检"],
}


@dataclass
class RiskResult:
    """风控判定结果"""
    score: float = 0.0
    decision: str = "pass"          # pass / review / blocked
    tags: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    hits: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "decision": self.decision,
            "tags": self.tags,
            "evidence": self.evidence,
            "hits": self.hits,
        }

    def as_text(self) -> str:
        """给 Job.risk_points 存的可读文本（JSON 字符串由调用方决定）"""
        if not self.evidence:
            return ""
        return "；".join(self.evidence)


def _norm(text: Optional[str]) -> str:
    return (text or "").strip().lower()


def _bump(result: RiskResult, score: float, tag: str, reason: str, **hits: Any) -> None:
    """取「最高分」而非累加：避免多条弱信号叠加出误判，也保证解释清晰"""
    if score > result.score:
        result.score = score
    if tag not in result.tags:
        result.tags.append(tag)
    result.evidence.append(reason)
    for k, v in hits.items():
        if v:
            result.hits[k] = v


# --------------------------------------------------------------
# R1 敏感词
# --------------------------------------------------------------
def _check_sensitive_words(text: str, result: RiskResult) -> None:
    for category, words in SENSITIVE_WORDS.items():
        matched = [w for w in words if w in text]
        if not matched:
            continue
        # 色情/违法类直接高置信拦截，其余给 0.85 仍属拦截区间
        score = 0.95 if category in ("色情低俗", "违法业务") else 0.85
        _bump(
            result, score, f"敏感词::{category}",
            f"命中{category}词：{'、'.join(matched[:5])}",
            sensitive_words=matched[:10], category=category,
        )


# --------------------------------------------------------------
# R2 联系方式
# --------------------------------------------------------------
def _check_contact(text: str, result: RiskResult) -> None:
    found = []
    for pattern, label in CONTACT_PATTERNS:
        for m in pattern.finditer(text):
            found.append(f"{label}「{m.group(0)}」")
    if found:
        _bump(
            result, 0.7, "违规引流::联系方式外泄",
            f"正文出现联系方式：{'、'.join(found[:3])}",
            contact=found[:5],
        )


# --------------------------------------------------------------
# R3 薪资异常
# --------------------------------------------------------------
_NUM_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _extract_numbers(text: str) -> List[float]:
    nums = []
    for m in _NUM_RE.finditer(text or ""):
        try:
            nums.append(float(m.group(1)))
        except ValueError:
            continue
    return nums


def estimate_monthly_salary(salary_text: Optional[str]) -> Optional[float]:
    """从自由文本薪资里粗估「月薪上限」，用于异常检测（只求量级，不求精确）"""
    text = _norm(salary_text)
    if not text:
        return None

    nums = _extract_numbers(text)
    if not nums:
        return None
    upper = max(nums)

    if "万" in text:
        upper *= 10000
    elif "k" in text or "千" in text:
        upper *= 1000

    if "日结" in text or "天" in text or "/日" in text:
        return upper * 26
    if "时" in text or "/小时" in text or "元/时" in text:
        return upper * 8 * 26
    if "周" in text:
        return upper * 4
    return upper


def _check_salary(salary_text: Optional[str], result: RiskResult) -> None:
    text = _norm(salary_text)
    monthly = estimate_monthly_salary(salary_text)

    if "日结" in text or "/日" in text:
        nums = _extract_numbers(text)
        daily = max(nums) if nums else None
        if daily and daily >= SALARY_DAILY_MAX:
            _bump(
                result, 0.65, "薪资异常::日结单价离谱",
                f"日结单价 {daily:g} 元/天，超过阈值 {SALARY_DAILY_MAX:g}",
                salary_daily=daily,
            )
            return

    if monthly and monthly >= SALARY_MONTHLY_MAX:
        _bump(
            result, 0.6, "薪资异常::月薪超阈值",
            f"估算月薪上限 {monthly:g} 元，超过阈值 {SALARY_MONTHLY_MAX:g}",
            salary_monthly=monthly,
        )


# --------------------------------------------------------------
# R4 经营范围不匹配
# --------------------------------------------------------------
def _detect_categories(text: str) -> List[str]:
    text = _norm(text)
    found = []
    for category, keywords in TITLE_CATEGORY.items():
        # 类目名本身也算命中（企业行业字段常直接写「零售」「餐饮」而不是具体关键词）
        if category in text or any(k in text for k in keywords):
            found.append(category)
    return found


def _check_category(title: str, industry: Optional[str], result: RiskResult) -> None:
    title_cats = _detect_categories(title)
    if not title_cats:
        return

    industry_cats = _detect_categories(industry or "")
    if not industry_cats:
        # 企业行业无法识别时不做判断，避免误伤
        return

    if set(title_cats).isdisjoint(set(industry_cats)):
        _bump(
            result, 0.55, "经营异常::岗位与行业不符",
            f"岗位类目【{'/'.join(title_cats)}】与企业行业【{'/'.join(industry_cats)}】明显不匹配",
            title_category=title_cats, industry_category=industry_cats,
        )


# --------------------------------------------------------------
# 对外入口
# --------------------------------------------------------------
def decide(score: float) -> str:
    if score >= BLOCK_THRESHOLD:
        return "blocked"
    if score >= REVIEW_THRESHOLD:
        return "review"
    return "pass"


def evaluate_job(
        title: Optional[str],
        description: Optional[str],
        requirement: Optional[str],
        salary: Optional[str],
        industry: Optional[str] = None,
        entity_name: Optional[str] = None,
) -> RiskResult:
    """对一条岗位做第一层规则判定。

    industry / entity_name 来自企业档案（CooperationEntity.ext_info['industry'] 等）。
    """
    result = RiskResult()

    body = " ".join(filter(None, [_norm(title), _norm(description), _norm(requirement)]))
    title_text = _norm(title)

    # 敏感词：标题权重更高，命中即在该分数基础上再上浮
    _check_sensitive_words(body, result)
    if result.tags and any(t.startswith("敏感词::") for t in result.tags) and title_text:
        # 标题里直接出现敏感词，属于刻意规避成本最低的情况，提升到 0.98
        for category, words in SENSITIVE_WORDS.items():
            if any(w in title_text for w in words):
                result.score = max(result.score, 0.98)
                if f"敏感词::{category}（标题）" not in result.tags:
                    result.tags.append(f"敏感词::{category}（标题）")
                result.evidence.append(f"标题直接包含{category}词")
                break

    _check_contact(body, result)
    _check_salary(salary, result)
    _check_category(title, industry or entity_name, result)

    result.score = min(result.score, 1.0)
    result.decision = decide(result.score)
    return result
