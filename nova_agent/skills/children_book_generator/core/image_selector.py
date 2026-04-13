"""
自动图像筛选模块
使用LLM视觉能力（如果可用）对生成的4张图进行初筛，选出最佳候选
用户只需要做最终确认
"""

from typing import List, Dict, Any, Optional
from PIL import Image
from nova_agent.llm.client_base import LLMClient


class AutoImageSelector:
    """自动图像筛选器
    
    当LLM支持视觉能力时，自动对每页生成的4张图进行筛选，
    选出最符合要求的1-2张候选，减少用户手动筛选工作量。"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def evaluate_candidates(
        self,
        candidate_paths: List[str],
        prompt: str,
        requirements: str = "",
    ) -> List[Dict[str, Any]]:
        """评估多个候选图片，打分排序
        
        参数：
        - candidate_paths: 候选图片路径列表
        - prompt: 原始生成提示词
        - requirements: 额外要求
        
        返回：
        - 打分后的候选列表，按分数从高到低排序
        """
        import base64
        from io import BytesIO
        
        # 对每个候选图编码
        encoded_images = []
        for path in candidate_paths:
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                encoded_images.append(encoded)
        
        # 构建评估prompt
        eval_prompt = self._build_evaluation_prompt(prompt, requirements, len(candidate_paths))
        
        # 如果LLM支持视觉，进行评估
        # 这里我们构建多模态prompt
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": eval_prompt},
                ] + [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                    for img in encoded_images
                ]
            }
        ]
        
        try:
            response = self.llm.chat(messages, temperature=0.3)
            return self._parse_evaluation(response, candidate_paths)
        except Exception as e:
            # 如果视觉不支持，返回原始顺序，用户手动选
            print(f"Visual evaluation not available: {e}, returning original order")
            return [{"path": p, "score": 50, "comment": "Automatic evaluation not available"} for p in candidate_paths]
    
    def _build_evaluation_prompt(self, prompt: str, requirements: str, num_candidates: int) -> str:
        return f"""你是儿童绘本插图编辑，请从{num_candidates}张候选图片中选出最符合要求的。

生成提示词：{prompt}

额外要求：{requirements}

评估标准：
1. 主角是否正确，特征是否符合描述
2. 构图是否正确，主角是否占据主要位置
3. 底部是否留出了足够的空白放文字
4. 是否有任何文字出现在图片上（不能有文字）
5. 背景是否简洁干净，突出主角
6. 整体风格是否符合儿童绘本

请按照以下JSON格式打分：

{{
  "evaluations": [
    {{
      "index": 图片编号(从0开始),
      "score": 分数0-100,
      "comment": "简短评价",
      "reject": true/false (不合格请true，比如有文字/主角错了)
    }},
    ...
  ],
  "top_recommendations": [推荐的编号列表，按推荐顺序排序，最多选2个]
}}

只输出JSON，不要其他内容：
"""
    
    def _parse_evaluation(self, response: str, candidate_paths: List[str]) -> List[Dict]:
        import json
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            evaluations = data.get("evaluations", [])
            
            # 补上路径
            for i, eval in enumerate(evaluations):
                idx = eval.get("index", i)
                eval["path"] = candidate_paths[idx]
            
            # 按分数排序，排除被reject的
            valid = [e for e in evaluations if not e.get("reject", False)]
            sorted_valid = sorted(valid, key=lambda x: x.get("score", 0), reverse=True)
            
            return sorted_valid
            
        except Exception as e:
            print(f"Failed to parse evaluation: {e}")
            # 解析失败返回原始顺序
            return [{"path": p, "score": 50, "comment": "Parsing failed"} for p in candidate_paths]
    
    def select_best(self, candidates: List[Dict]) -> Optional[str]:
        """从评估后的候选中选出最佳"""
        if not candidates:
            return None
        return candidates[0]["path"]
    
    def get_top_two(self, candidates: List[Dict]) -> List[str]:
        """获取前两名候选"""
        sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
        return [c["path"] for c in sorted_candidates[:2]]
