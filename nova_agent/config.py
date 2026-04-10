"""
Configuration - 默认配置

支持自定义配置，多级配置覆盖，支持自主进化调整参数。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Nova Agent 配置
    
    所有参数都在这里统一管理，支持：
    1. 默认合理值
    2. 用户覆盖配置
    3. 自主进化根据反馈调整
    4. 配置持久化保存
    """
    
    # ========== 记忆配置 ==========
    memory_data_dir: str = "./data/nova-agent/memory"
    """记忆数据存储目录"""
    
    vector_backend: str = "chromadb"
    """向量存储后端: chromadb / memory"""
    
    # ========== HGARN 推理核心配置 ==========
    block_size: int = 8
    """每个块最大子任务数（遵循 7±2 认知法则）"""
    
    max_blocks_per_level: int = 2
    """每个层级最多允许多少个块（控制 token 增长）"""
    
    max_levels: int = 3
    """最大推理层级，超过停止聚合"""
    
    cumulative_gain_threshold: float = 2.5
    """累积信息增益达到这个值提前停止，节省 token"""
    
    enable_vector_prefilter: bool = True
    """是否开启向量预过滤，减少 LLM 调用"""
    
    vector_similarity_threshold: float = 0.3
    """向量相似度低于这个值会被过滤掉"""
    
    min_gate_for_continue: float = 0.15
    """继续下一层级需要的最小门控分数"""
    
    # 双向注意力流配置
    enable_reverse_activation: bool = True
    """是否启用双向注意力流（上层反向激活下层）"""
    
    reverse_activation_gain_threshold: float = 0.3
    """反向激活需要的最小信息增益阈值"""
    
    # 门控配置
    gate_at_block_level: bool = False
    """是否在 block 级别计算门控（false = 只在层级计算，节省 token）"""
    
    enable_recursive_decomposition: bool = True
    """是否允许递归分解任务"""
    
    max_recursion_depth: int = 3
    """最大递归深度"""
    
    # WTA 和侧抑制配置
    wta_max_activate: int = 7
    """WTA 赢者通吃最大激活数量（7±2 认知法则）"""
    
    lateral_inhibition_enabled: bool = True
    """是否启用自适应侧抑制"""
    
    lateral_inhibition_base_strength: float = 0.2
    """侧抑制基础强度"""
    
    # ========== 并发执行配置 ==========
    enable_dynamic_concurrency: bool = True
    """是否启用动态并发控制"""
    
    min_concurrency: int = 1
    """最小并发数"""
    
    max_concurrency: int = 8
    """最大并发数"""
    
    exponential_backoff_base: float = 2.0
    """指数退避底数"""
    
    # ========== 沙箱执行配置 ==========
    sandbox_type: str = "local"
    """沙箱类型: local / docker"""
    
    sandbox_config: Dict[str, Any] = None
    """沙箱特定配置"""
    
    # ========== LLM 配置 ==========
    llm_provider: str = "openclaw"
    """LLM 提供者: openclaw / openai / anthropic"""
    
    llm_config: Dict[str, Any] = None
    """LLM 特定配置（model, api_key 等）"""
    
    max_tokens_per_completion: int = 4096
    """每次补全最大 token 数"""
    
    default_temperature: float = 0.7
    """默认温度参数"""
    
    # ========== 进化配置 ==========
    evolution_enabled: bool = True
    """是否启用自主进化"""
    
    auto_optimize_config: bool = True
    """是否根据反馈自动优化配置参数"""
    
    min_quality_for_learning: float = 0.8
    """学习技能需要的最低质量分数"""
    
    # ========== 技能遗忘配置 ==========
    skill_forgetting_enabled: bool = True
    """是否启用自适应技能遗忘"""
    
    skill_forgetting_decay: float = 0.01
    """遗忘指数（越大遗忘越快）"""
    
    # ========== 工作记忆配置 ==========
    enable_working_memory_partition: bool = True
    """是否启用工作记忆分区（减少干扰）"""
    
    def __post_init__(self):
        if self.sandbox_config is None:
            self.sandbox_config = {}
        if self.llm_config is None:
            self.llm_config = {}
    
    @classmethod
    def default(cls) -> 'Config':
        """默认配置（经过优化的推荐值）"""
        return cls()
    
    @classmethod
    def conservative(cls) -> 'Config':
        """保守配置（更深度处理，token 更多但质量更高）"""
        return cls(
            max_levels=4,
            cumulative_gain_threshold=3.5,
            block_size=10,
            max_blocks_per_level=3,
            wta_max_activate=9
        )
    
    @classmethod
    def efficient(cls) -> 'Config':
        """高效配置（节省 token，快速响应）"""
        return cls(
            max_levels=2,
            cumulative_gain_threshold=1.5,
            block_size=6,
            max_blocks_per_level=2,
            wta_max_activate=5
        )
    
    def update(self, config: Dict[str, Any]) -> None:
        """更新配置，支持部分覆盖"""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")
    
    def apply_evolution(self, quality_score: float) -> Dict[str, Any]:
        """
        根据质量反馈自主进化调整配置
        
        Args:
            quality_score: 质量分数 0-1
        
        Returns:
            变更字典，记录哪些参数被修改
        """
        changes = {}
        original = self.to_dict()
        
        if quality_score < 0.3:
            # 质量很低，需要更深层次处理
            if self.max_levels < 5:
                self.max_levels += 1
                changes['max_levels'] = (original['max_levels'], self.max_levels)
            self.cumulative_gain_threshold += 0.5
            changes['cumulative_gain_threshold'] = (
                original['cumulative_gain_threshold'], 
                self.cumulative_gain_threshold
            )
            logger.info(f"Low quality score {quality_score:.2f}: increased processing depth")
        
        elif quality_score > 0.9:
            # 质量很好，可以尝试更高效处理
            if self.max_levels > 2:
                self.max_levels -= 1
                changes['max_levels'] = (original['max_levels'], self.max_levels)
            if self.cumulative_gain_threshold > 1.0:
                self.cumulative_gain_threshold -= 0.3
                changes['cumulative_gain_threshold'] = (
                    original['cumulative_gain_threshold'], 
                    self.cumulative_gain_threshold
                )
            logger.info(f"High quality score {quality_score:.2f}: decreased processing depth for efficiency")
        
        # 调整侧抑制强度
        if 0.3 <= quality_score <= 0.7:
            # 质量一般，增加抑制去重
            self.lateral_inhibition_base_strength += 0.05
            changes['lateral_inhibition_base_strength'] = (
                original['lateral_inhibition_base_strength'],
                self.lateral_inhibition_base_strength
            )
        
        return changes
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """从字典创建"""
        return cls(**data)
    
    def save(self, path: str) -> None:
        """保存配置到文件"""
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Config saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'Config':
        """从文件加载配置"""
        if not os.path.exists(path):
            logger.info(f"Config file {path} not found, using defaults")
            return cls.default()
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = cls.from_dict(data)
        logger.info(f"Config loaded from {path}")
        return config
    
    def get_evolution_summary(self, original: Dict[str, Any]) -> str:
        """生成进化变更摘要"""
        current = self.to_dict()
        changes = []
        
        for key, value in current.items():
            if key in original and original[key] != value:
                changes.append(f"- {key}: {original[key]} → {value}")
        
        if not changes:
            return "No configuration changes"
        
        return "**Configuration changes from evolution:**\n" + "\n".join(changes)
