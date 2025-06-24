#!/usr/bin/env python3
"""
代码仓库获取器使用示例

演示如何使用 RepositoryFetcher 从不同来源获取代码仓库
"""

import logging
from pathlib import Path

from coderepoindex.repository import (
    RepositoryFetcher, 
    create_git_config, 
    create_local_config, 
    create_zip_config
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_git_repository():
    """演示从 Git 仓库获取代码"""
    print("\n=== Git 仓库获取示例 ===")
    
    # 演示默认克隆到 .coderepo 目录
    with RepositoryFetcher() as fetcher:
        # 示例1: 克隆主分支（不指定目标目录，将克隆到 .coderepo/Hello-World）
        config = create_git_config(
            repo_url="https://github.com/octocat/Hello-World.git",
            branch="master"
        )
        
        try:
            repo_path = fetcher.fetch(config)
            print(f"仓库克隆到: {repo_path}")
            
            # 检查仓库内容
            repo_dir = Path(repo_path)
            files = list(repo_dir.glob("*"))
            print(f"仓库文件: {[f.name for f in files[:5]]}")  # 显示前5个文件
            
        except Exception as e:
            print(f"获取失败: {e}")
    
    # 示例2: 克隆特定标签
    with RepositoryFetcher() as fetcher:
        config = create_git_config(
            repo_url="https://github.com/python/cpython.git",
            tag="v3.11.0",  # 克隆特定标签
            target_dir="./temp/cpython_v3.11.0"  # 指定目标目录
        )
        
        try:
            repo_path = fetcher.fetch(config)
            print(f"CPython v3.11.0 克隆到: {repo_path}")
            
        except Exception as e:
            print(f"获取 CPython 失败: {e}")


def demo_local_repository():
    """演示使用本地仓库"""
    print("\n=== 本地仓库获取示例 ===")
    
    # 使用当前项目作为示例
    current_project = Path(__file__).parent.parent
    
    with RepositoryFetcher() as fetcher:
        config = create_local_config(str(current_project))
        
        try:
            repo_path = fetcher.fetch(config)
            print(f"本地仓库路径: {repo_path}")
            
            # 检查项目结构
            repo_dir = Path(repo_path)
            dirs = [d.name for d in repo_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            print(f"项目目录: {dirs}")
            
        except Exception as e:
            print(f"获取本地仓库失败: {e}")


def demo_zip_repository():
    """演示从 ZIP 文件获取代码"""
    print("\n=== ZIP 文件获取示例 ===")
    
    # 注意：这里只是演示，实际需要有一个 ZIP 文件
    zip_path = "./example_repo.zip"
    
    if not Path(zip_path).exists():
        print(f"ZIP 文件不存在: {zip_path}")
        print("您可以下载任何项目的 ZIP 包来测试此功能")
        return
    
    with RepositoryFetcher() as fetcher:
        config = create_zip_config(
            zip_path=zip_path,
            target_dir="./temp/extracted_repo"
        )
        
        try:
            repo_path = fetcher.fetch(config)
            print(f"ZIP 仓库解压到: {repo_path}")
            
            # 检查解压的内容
            repo_dir = Path(repo_path)
            files = list(repo_dir.glob("*"))
            print(f"解压的文件: {[f.name for f in files[:10]]}")
            
        except Exception as e:
            print(f"获取 ZIP 仓库失败: {e}")


def demo_commit_based_directory_naming():
    """演示基于 commit_id 的目录命名和复用"""
    print("\n=== 基于 commit_id 的目录管理示例 ===")
    
    with RepositoryFetcher() as fetcher:
        # 1. 获取同一仓库的不同分支（会产生不同的commit_id）
        print("\n1. 同一仓库的不同分支:")
        
        # 主分支
        config_main = create_git_config(
            repo_url="https://github.com/octocat/Hello-World.git",
            branch="master"
        )
        
        try:
            path_main = fetcher.fetch(config_main)
            print(f"主分支路径: {path_main}")
            
            # 再次获取主分支，应该直接复用现有目录
            print("\n2. 再次获取主分支（应该复用现有目录）:")
            path_main_2 = fetcher.fetch(config_main)
            print(f"再次获取主分支: {path_main_2}")
            print(f"路径相同（复用成功）: {path_main == path_main_2}")
            
        except Exception as e:
            print(f"主分支测试出错: {e}")
        
        # 2. 测试指定具体commit
        print("\n3. 指定具体commit:")
        config_commit = create_git_config(
            repo_url="https://github.com/octocat/Hello-World.git",
            commit="553c2077f0edc3d5dc5d17262f6aa498e69d6f8e"  # Hello-World 的第一个commit
        )
        
        try:
            path_commit = fetcher.fetch(config_commit)
            print(f"指定commit路径: {path_commit}")
            
            # 再次获取相同commit，应该复用
            print("\n4. 再次获取相同commit（应该复用）:")
            path_commit_2 = fetcher.fetch(config_commit)
            print(f"再次获取相同commit: {path_commit_2}")
            print(f"路径相同（复用成功）: {path_commit == path_commit_2}")
            
        except Exception as e:
            print(f"commit测试出错: {e}")
        
        # 3. 演示不同commit产生不同目录
        print("\n5. 不同commit产生不同目录:")
        config_another_commit = create_git_config(
            repo_url="https://github.com/octocat/Hello-World.git",
            commit="7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"  # 另一个commit
        )
        
        try:
            path_another = fetcher.fetch(config_another_commit)
            print(f"另一个commit路径: {path_another}")
            print(f"与第一个commit不同: {path_commit != path_another}")
            
            # 显示目录结构
            from pathlib import Path
            coderepo_dir = Path.cwd() / ".coderepo"
            if coderepo_dir.exists():
                hello_world_dirs = [d.name for d in coderepo_dir.iterdir() 
                                  if d.is_dir() and d.name.startswith('Hello-World')]
                print(f"Hello-World相关目录: {hello_world_dirs}")
            
        except Exception as e:
            print(f"另一个commit测试出错: {e}")


def demo_advanced_git_usage():
    """演示高级 Git 使用场景"""
    print("\n=== 高级 Git 使用示例 ===")
    
    with RepositoryFetcher() as fetcher:
        # 克隆特定提交
        config = create_git_config(
            repo_url="https://github.com/torvalds/linux.git",
            commit="v6.1",  # 克隆特定提交
            target_dir="./temp/linux_v6.1"
        )
        
        try:
            repo_path = fetcher.fetch(config)
            print(f"Linux 内核 v6.1 克隆到: {repo_path}")
            
        except Exception as e:
            print(f"获取 Linux 内核失败: {e}")


def main():
    """运行所有示例"""
    print("CodeRepoIndex 仓库获取器示例")
    print("=" * 50)
    
    # 演示不同的获取方式
    demo_local_repository()              # 先演示本地，因为最可靠
    demo_git_repository()                # Git 示例，需要网络
    demo_commit_based_directory_naming() # 新特性：基于commit_id的目录管理
    demo_zip_repository()                # ZIP 示例，需要 ZIP 文件
    
    # 高级用法（可能比较慢）
    # demo_advanced_git_usage()
    
    print("\n演示完成！")


if __name__ == "__main__":
    main() 