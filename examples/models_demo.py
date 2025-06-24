"""
模型模块使用示例

演示如何使用 LLM 和 Embedding 模型提供商
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from coderepoindex.models import (
    create_openai_providers,
    create_llm_provider,
    create_embedding_provider,
    ModelFactory,
    setup_model_logging
)

# 设置日志
setup_model_logging()


def demo_unified_openai_provider():
    """演示统一的 OpenAI 提供商用法"""
    print("=== 统一 OpenAI 提供商示例 ===")
    
    # 注意：这里需要实际的 API key 和 base_url
    # 为了示例，使用占位符
    try:
        provider = create_openai_providers(
            api_key="your-api-key-here",
            base_url="https://your-api-endpoint.com/v1",
            llm_model="qwen-plus",
            embedding_model="text-embedding-3-small"
        )
        
        # 获取 LLM 提供商
        llm = provider.get_llm_provider()
        print(f"LLM 模型: {llm.get_model_name()}")
        
        # 获取 Embedding 提供商
        embedding = provider.get_embedding_provider()
        print(f"Embedding 模型: {embedding.get_model_name()}")
        print(f"最大输入长度: {embedding.get_max_input_length()}")
        
        # 测试 LLM（如果有真实的 API key）
        if False:  # 设置为 True 来测试真实 API
            messages = [
                {"role": "user", "content": "你好，请简单介绍一下你自己。"}
            ]
            response = llm.chat_completion(messages)
            print(f"LLM 响应: {response}")
            
            # 测试 Embedding
            text = "这是一个测试文本"
            embeddings = embedding.get_embedding(text)
            print(f"Embedding 维度: {len(embeddings)}")
        
    except Exception as e:
        print(f"统一提供商示例失败: {e}")


def demo_separate_providers():
    """演示分别创建 LLM 和 Embedding 提供商"""
    print("\n=== 分别创建提供商示例 ===")
    
    try:
        # 创建 LLM 提供商
        llm_provider = create_llm_provider(
            provider_type="api",
            model_name="qwen-plus",
            api_key="your-api-key-here",
            base_url="https://your-api-endpoint.com/v1"
        )
        print(f"LLM 提供商创建成功: {llm_provider.get_model_name()}")
        
        # 创建 Embedding 提供商
        embedding_provider = create_embedding_provider(
            provider_type="api",
            model_name="text-embedding-3-small",
            api_key="your-api-key-here",
            base_url="https://your-api-endpoint.com/v1"
        )
        print(f"Embedding 提供商创建成功: {embedding_provider.get_model_name()}")
        
    except Exception as e:
        print(f"分别创建提供商失败: {e}")


def demo_factory_methods():
    """演示工厂方法的使用"""
    print("\n=== 工厂方法示例 ===")
    
    try:
        # 使用工厂方法创建 LLM 提供商
        llm = ModelFactory.create_llm_provider(
            provider_type="api",
            model_name="qwen-plus",
            api_key="your-api-key-here",
            base_url="https://your-api-endpoint.com/v1"
        )
        print(f"工厂方法创建 LLM: {llm.get_model_name()}")
        
        # 使用工厂方法创建 Embedding 提供商
        embedding = ModelFactory.create_embedding_provider(
            provider_type="api", 
            model_name="text-embedding-3-small",
            api_key="your-api-key-here",
            base_url="https://your-api-endpoint.com/v1"
        )
        print(f"工厂方法创建 Embedding: {embedding.get_model_name()}")
        
    except Exception as e:
        print(f"工厂方法示例失败: {e}")


def demo_local_providers():
    """演示本地提供商（目前为空实现）"""
    print("\n=== 本地提供商示例 ===")
    
    try:
        # 尝试创建本地 LLM 提供商
        local_llm = create_llm_provider(
            provider_type="local",
            model_name="local-model",
            model_path="/path/to/local/model"
        )
        print(f"本地 LLM 提供商可用: {local_llm.is_available()}")
        
        # 尝试创建本地 Embedding 提供商
        local_embedding = create_embedding_provider(
            provider_type="local",
            model_name="local-embedding",
            model_path="/path/to/local/embedding"
        )
        print(f"本地 Embedding 提供商可用: {local_embedding.is_available()}")
        
    except Exception as e:
        print(f"本地提供商示例失败: {e}")


def demo_stream_completion():
    """演示流式聊天补全"""
    print("\n=== 流式聊天补全示例 ===")
    
    try:
        provider = create_openai_providers(
            api_key="your-api-key-here",
            base_url="https://your-api-endpoint.com/v1"
        )
        
        llm = provider.get_llm_provider()
        
        if False:  # 设置为 True 来测试真实 API
            messages = [
                {"role": "user", "content": "请写一首简短的诗"}
            ]
            
            print("流式响应:")
            for chunk in llm.stream_chat_completion(messages):
                print(chunk, end="", flush=True)
            print("\n")
        else:
            print("流式聊天补全需要真实的 API 配置")
            
    except Exception as e:
        print(f"流式补全示例失败: {e}")


def demo_batch_embeddings():
    """演示批量 embedding"""
    print("\n=== 批量 Embedding 示例 ===")
    
    try:
        provider = create_openai_providers(
            api_key="your-api-key-here",
            base_url="https://your-api-endpoint.com/v1"
        )
        
        embedding = provider.get_embedding_provider()
        
        if False:  # 设置为 True 来测试真实 API
            texts = [
                "这是第一个文本",
                "这是第二个文本",
                "这是第三个文本"
            ]
            
            embeddings = embedding.get_embeddings_batch(texts)
            print(f"批量处理了 {len(embeddings)} 个文本")
            for i, emb in enumerate(embeddings):
                print(f"文本 {i+1} 的 embedding 维度: {len(emb)}")
        else:
            print("批量 embedding 需要真实的 API 配置")
            
    except Exception as e:
        print(f"批量 embedding 示例失败: {e}")


if __name__ == "__main__":
    print("模型模块使用示例")
    print("=" * 50)
    
    # 运行所有示例
    demo_unified_openai_provider()
    demo_separate_providers()
    demo_factory_methods()
    demo_local_providers()
    demo_stream_completion()
    demo_batch_embeddings()
    
    print("\n" + "=" * 50)
    print("示例完成")
    print("\n注意：")
    print("1. 要测试真实的 API 调用，请提供正确的 api_key 和 base_url")
    print("2. 本地模型提供商目前为空实现，需要后续扩展")
    print("3. 可以根据需要扩展支持更多的模型提供商（如 HuggingFace、Ollama 等）") 