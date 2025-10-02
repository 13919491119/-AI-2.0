
from enum import Enum, auto

# 任务状态枚举
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    # ... 其他状态

# 学习周期枚举
class LearningCycle(Enum):
    INITIAL = "initial"
    TRAINING = "training"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"
    # ... 其他周期

# ==================== 核心枚举定义 ====================

class TaskType(Enum):
    LIUREN_PREDICTION = auto()
    LIUYAO_ANALYSIS = auto()
    CULTURAL_PROBABILITY = auto()
    REWARD_EVALUATION = auto()
    PATTERN_LEARNING = auto()
    SYSTEM_OPTIMIZATION = auto()
    # ... 其他枚举值

class LiurenPalm(Enum):
    DAAN = "大安"
    LIULIAN = "留连"
    SUXI = "速喜"
    CHIKOU = "赤口"
    XIAOJI = "小吉"
    KONGWANG = "空亡"

class LearningMode(Enum):
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    UNSUPERVISED = "unsupervised"
    # ... 其他学习模式

class UpgradeStatus(Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    PLANNING = "planning"
    EXECUTING = "executing"
    # ... 其他升级状态

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class CulturalDomain(Enum):
    PHILOSOPHY = "philosophy"
    ART = "art"
    SCIENCE = "science"
    RELIGION = "religion"
    # ... 其他文化领域

class YaoType(Enum):
    YANG = "阳爻"
    YIN = "阴爻"
    OLD_YANG = "老阳"
    OLD_YIN = "老阴"
    # ... 其他爻类型

class AdaptationStrategy(Enum):
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    # ... 其他适应策略
