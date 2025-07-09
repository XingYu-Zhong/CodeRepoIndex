#!/bin/bash

# 测试文档构建脚本
# Test documentation build script

set -e

echo "🚀 开始测试文档构建..."
echo "🚀 Starting documentation build test..."

# 检查是否安装了必要的依赖
echo "📋 检查依赖..."
echo "📋 Checking dependencies..."

if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装"
    echo "❌ Python is not installed"
    exit 1
fi

# 安装文档依赖
echo "📦 安装文档依赖..."
echo "📦 Installing documentation dependencies..."
pip install -e ".[docs]"

# 清理之前的构建
echo "🧹 清理之前的构建..."
echo "🧹 Cleaning previous builds..."
rm -rf docs/_build/

# 构建文档
echo "🔨 构建 HTML 文档..."
echo "🔨 Building HTML documentation..."
cd docs && sphinx-build -b html . _build/html -W --keep-going

echo "✅ 文档构建成功！"
echo "✅ Documentation build successful!"
echo "📁 输出目录: docs/_build/html/"
echo "📁 Output directory: docs/_build/html/"
echo "🌐 使用浏览器打开 docs/_build/html/index.html 查看文档"
echo "🌐 Open docs/_build/html/index.html in your browser to view the documentation" 