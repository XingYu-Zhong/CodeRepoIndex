"""
CodeRepoIndex 命令行接口

提供便捷的命令行工具来创建索引和搜索代码。
"""

import click
import logging
from pathlib import Path
from typing import Optional

from .core.indexer import CodeIndexer
from .core.searcher import CodeSearcher

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@click.group()
@click.version_option()
def cli():
    """CodeRepoIndex - 通过语义理解提高代码仓库的可发现性和可搜索性"""
    pass


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option(
    "--language", "-l",
    help="指定编程语言"
)
@click.option(
    "--exclude", "-e",
    multiple=True,
    help="排除文件模式"
)
@click.option(
    "--storage-backend", "-s",
    default="chroma",
    help="存储后端类型"
)
@click.option(
    "--embedding-model", "-m",
    default="sentence-transformers/all-MiniLM-L6-v2",
    help="嵌入模型名称"
)
def index(
    repo_path: str,
    language: Optional[str],
    exclude: tuple,
    storage_backend: str,
    embedding_model: str
):
    """为代码仓库创建索引"""
    click.echo(f"🚀 开始为仓库创建索引: {repo_path}")
    
    indexer = CodeIndexer(
        embedding_model=embedding_model,
        storage_backend=storage_backend
    )
    
    try:
        stats = indexer.index_repository(
            repo_path=repo_path,
            language=language,
            exclude_patterns=list(exclude) if exclude else None
        )
        
        click.echo("✅ 索引创建完成！")
        click.echo(f"📊 统计信息:")
        click.echo(f"  - 总文件数: {stats['total_files']}")
        click.echo(f"  - 已索引文件: {stats['indexed_files']}")
        click.echo(f"  - 代码块数: {stats['code_blocks']}")
        click.echo(f"  - 生成向量数: {stats['vectors_created']}")
        
    except Exception as e:
        click.echo(f"❌ 索引创建失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("query")
@click.option(
    "--top-k", "-k",
    default=10,
    help="返回结果数量"
)
@click.option(
    "--language", "-l",
    help="限制搜索的编程语言"
)
@click.option(
    "--threshold", "-t",
    default=0.0,
    help="相似度阈值"
)
@click.option(
    "--storage-backend", "-s",
    default="chroma",
    help="存储后端类型"
)
@click.option(
    "--embedding-model", "-m",
    default="sentence-transformers/all-MiniLM-L6-v2",
    help="嵌入模型名称"
)
def search(
    query: str,
    top_k: int,
    language: Optional[str],
    threshold: float,
    storage_backend: str,
    embedding_model: str
):
    """搜索相似代码块"""
    click.echo(f"🔍 搜索查询: '{query}'")
    
    searcher = CodeSearcher(
        storage_backend=storage_backend,
        embedding_model=embedding_model
    )
    
    try:
        results = searcher.search(
            query=query,
            top_k=top_k,
            language=language,
            similarity_threshold=threshold
        )
        
        if not results:
            click.echo("😔 没有找到相关结果")
            return
        
        click.echo(f"✅ 找到 {len(results)} 个相关结果:")
        
        for i, result in enumerate(results, 1):
            click.echo(f"\n📄 结果 {i}:")
            click.echo(f"  文件: {result.file_path}")
            click.echo(f"  行数: {result.line_start}-{result.line_end}")
            click.echo(f"  相似度: {result.similarity_score:.3f}")
            if result.language:
                click.echo(f"  语言: {result.language}")
            click.echo(f"  代码:")
            click.echo(f"    {result.code_snippet[:100]}...")
            
    except Exception as e:
        click.echo(f"❌ 搜索失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--storage-backend", "-s",
    default="chroma",
    help="存储后端类型"
)
def stats(storage_backend: str):
    """显示索引统计信息"""
    click.echo("📊 索引统计信息:")
    
    searcher = CodeSearcher(storage_backend=storage_backend)
    stats_data = searcher.get_stats()
    
    click.echo(f"  - 总向量数: {stats_data['total_indexed_blocks']}")
    click.echo(f"  - 支持语言: {', '.join(stats_data['available_languages']) or '无'}")
    click.echo(f"  - 索引大小: {stats_data['index_size']}")
    click.echo(f"  - 最后更新: {stats_data['last_updated'] or '从未'}")


def main():
    """主入口函数"""
    cli()


if __name__ == "__main__":
    main() 