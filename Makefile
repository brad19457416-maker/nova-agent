.PHONY: help install install-dev test test-cov lint format type-check clean build

help:
	@echo "Nova Agent 开发命令"
	@echo ""
	@echo "  make install      - 安装生产依赖"
	@echo "  make install-dev  - 安装开发依赖"
	@echo "  make test         - 运行测试"
	@echo "  make test-cov     - 运行测试并生成覆盖率报告"
	@echo "  make lint         - 运行代码检查"
	@echo "  make format       - 格式化代码"
	@echo "  make type-check   - 运行类型检查"
	@echo "  make build        - 构建包"
	@echo "  make clean        - 清理构建文件"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=nova_agent --cov-report=term --cov-report=html

lint:
	ruff check nova_agent/ tests/
	black --check nova_agent/ tests/

format:
	black nova_agent/ tests/
	ruff check --fix nova_agent/ tests/

type-check:
	mypy nova_agent/ --ignore-missing-imports

build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
