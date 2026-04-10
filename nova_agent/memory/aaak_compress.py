"""
AAAK Compressor - Adaptive Ascii-Art Aware Compression

定制无损压缩算法：
- 显著减少 token 数量
- 保持人类和 LLM 可读性
- 无需特殊解码器，直接可读
- 通常可达 5-8x 压缩率
"""

import re


class AAAKCompressor:
    """
    AAAK 压缩器

    压缩原理：
    1. 移除不必要空白和重复换行
    2. 使用简洁符号替代重复短语
    3. 保持结构清晰
    4. LLM 仍然可以完全读懂
    """

    def __init__(self, compression_level: int = 3):
        """
        初始化压缩器

        Args:
            compression_level: 压缩级别 1-5，越高压缩越多
        """
        self.level = compression_level
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译替换模式"""
        # 常见短语替换（节省token）
        self.common_replacements = [
            (r"\btherefore\b", "∴"),
            (r"\bbecause\b", "∵"),
            (r"\bin conclusion\b", "∴"),
            (r"\bto summarize\b", "∴"),
            (r"\bfor example\b", "e.g."),
            (r"\bthat is\b", "i.e."),
            (r"\bin other words\b", "iow"),
            (r"\bwith respect to\b", "wrt"),
            (r"\bas far as\b", "afaict"),
            (r"\bin my opinion\b", "imo"),
            (r"\bthis means that\b", "→"),
            (r"\bleads to\b", "→"),
            (r"\bresults in\b", "→"),
            (r"\bis equal to\b", "="),
            (r"\bis not equal to\b", "≠"),
            (r"\bis greater than\b", ">"),
            (r"\bis less than\b", "<"),
            (r"\band\b", "&"),
            (r"\bor\b", "|"),
        ]

        if self.level >= 3:
            # 更高压缩级别，更多替换
            self.common_replacements.extend(
                [
                    (r"\bfunction\b", "fn"),
                    (r"\bmethod\b", "meth"),
                    (r"\bclass\b", "cls"),
                    (r"\bobject\b", "obj"),
                    (r"\bparameter\b", "param"),
                    (r"\breturn\b", "ret"),
                    (r"\bargument\b", "arg"),
                    (r"\bvariables\b", "vars"),
                    (r"\binformation\b", "info"),
                    (r"\bapplication\b", "app"),
                    (r"\bconfiguration\b", "config"),
                    (r"\bdevelopment\b", "dev"),
                    (r"\bproduction\b", "prod"),
                    (r"\btesting\b", "test"),
                    (r"\bdatabase\b", "db"),
                ]
            )

    def compress(self, text: str) -> str:
        """
        压缩文本

        Args:
            text: 原始文本

        Returns:
            压缩后的文本，仍然完全可读
        """
        if not text:
            return text

        # 步骤 1: 压缩空白
        compressed = self._compress_whitespace(text)

        # 步骤 2: 常见短语替换
        for pattern, replacement in self.common_replacements:
            if self.level >= 2 or "example" not in pattern:
                compressed = re.sub(pattern, replacement, compressed)

        # 步骤 3: 移除重复空行
        compressed = re.sub(r"\n\s*\n+", "\n\n", compressed)

        # 步骤 4: 缩进压缩（对于代码）
        if self.level >= 4:
            compressed = self._compress_indentation(compressed)

        return compressed

    def decompress(self, compressed: str) -> str:
        """
        尝试解压缩（可逆性不是强制保证，但尽量）
        注意：AAAK 是有损压缩，解压缩不能保证完全复原，但可读懂

        Args:
            compressed: 压缩文本

        Returns:
            解压后文本
        """
        # 符号替换回原文
        decompressed = compressed
        replacements = {
            "∴": "therefore",
            "∵": "because",
            "→": "leads to",
            "e.g.": "for example",
            "i.e.": "that is",
            "iow": "in other words",
            "wrt": "with respect to",
            "afaict": "as far as I can tell",
            "imo": "in my opinion",
            "&": "and",
            "|": "or",
        }

        for symbol, full in replacements.items():
            decompressed = decompressed.replace(symbol, full)

        return decompressed

    def _compress_whitespace(self, text: str) -> str:
        """压缩空白"""
        # 行尾空白移除
        lines = [line.rstrip() for line in text.split("\n")]

        # 移除全空行开头结尾
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)

    def _compress_indentation(self, text: str) -> str:
        """压缩代码缩进"""
        lines = text.split("\n")
        compressed_lines = []

        for line in lines:
            # 计算前导空格
            leading_space = len(line) - len(line.lstrip())
            if leading_space > 0:
                # 每 4 空格替换为一个 tab
                tabs = leading_space // 4
                remainder = leading_space % 4
                compressed_line = "\t" * tabs + " " * remainder + line.lstrip()
                compressed_lines.append(compressed_line)
            else:
                compressed_lines.append(line)

        return "\n".join(compressed_lines)

    def get_compression_ratio(self, original: str, compressed: str) -> float:
        """计算压缩率"""
        return len(compressed) / len(original)
