.PHONY: help install install-dev test lint format clean docs build publish

# 默认目标
help: ## 显示帮助信息
	@echo "可用的命令："
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## 安装项目依赖
	pip install -r requirements.txt

install-dev: ## 安装开发环境依赖
	pip install -e ".[dev]"
	pre-commit install

test: ## 运行测试
	pytest tests/ -v --cov=coderepoindex --cov-report=term-missing

test-fast: ## 运行快速测试（不包括集成测试）
	pytest tests/unit/ -v

lint: ## 代码质量检查
	black --check coderepoindex/
	isort --check-only coderepoindex/
	flake8 coderepoindex/
	mypy coderepoindex/
	bandit -r coderepoindex/

format: ## 格式化代码
	black coderepoindex/
	isort coderepoindex/

clean: ## 清理临时文件
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

docs: ## 构建文档
	cd docs && make html

docs-serve: ## 启动文档服务器
	cd docs/_build/html && python -m http.server 8000

build: clean ## 构建分发包
	python -m build

publish: build ## 发布到 PyPI
	twine upload dist/*

dev-setup: ## 完整的开发环境设置
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && make install-dev
	@echo "开发环境设置完成！"
	@echo "请运行: source venv/bin/activate"

security: ## 安全检查
	safety check
	bandit -r coderepoindex/

check: lint test ## 运行所有检查

ci: clean install-dev lint test security ## CI 流水线任务 