"""
Nova Agent 配置系统
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    palace_levels: int = 5  # 五级宫殿
    enable_temporal_graph: bool = True
    storage_path: str = "./data/memory"
    max_entries_per_level: int = 1000
    compression_threshold: int = 100  # 超过此数量触发压缩


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "openclaw"  # 默认使用OpenClaw
    model: str = "qwen2.5:7b"
    base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 120


@dataclass
class ReasoningConfig:
    """推理引擎配置"""
    enable_hgarn: bool = True
    attention_layers: int = 3
    gate_threshold: float = 0.5
    early_stop_gain: float = 0.01
    max_reasoning_depth: int = 5


@dataclass
class EvolutionConfig:
    """进化系统配置"""
    enabled: bool = True
    feedback_threshold: int = 10  # 收集多少反馈后触发进化
    auto_optimize: bool = True
    backup_before_evolve: bool = True


@dataclass
class CollaborationConfig:
    """协作模式配置"""
    default_mode: str = "direct"  # direct, lead_sub, swarm, agency
    max_sub_agents: int = 5
    swarm_size: int = 3


@dataclass
class ExecutionConfig:
    """执行环境配置"""
    use_docker: bool = False  # MVP版本暂不用Docker
    sandbox_enabled: bool = True
    timeout: int = 300
    max_memory_mb: int = 512


@dataclass
class NovaConfig:
    """Nova Agent 全局配置"""
    name: str = "Nova"
    version: str = "0.1.0"
    
    # 子系统配置
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    collaboration: CollaborationConfig = field(default_factory=CollaborationConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    
    # 调试选项
    debug: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "NovaConfig":
        """从环境变量加载配置"""
        config = cls()
        
        # LLM配置
        if os.getenv("LLM_MODEL"):
            config.llm.model = os.getenv("LLM_MODEL")
        if os.getenv("LLM_BASE_URL"):
            config.llm.base_url = os.getenv("LLM_BASE_URL")
        if os.getenv("LLM_API_KEY"):
            config.llm.api_key = os.getenv("LLM_API_KEY")
            
        # 调试
        if os.getenv("NOVA_DEBUG"):
            config.debug = os.getenv("NOVA_DEBUG").lower() == "true"
            
        return config
