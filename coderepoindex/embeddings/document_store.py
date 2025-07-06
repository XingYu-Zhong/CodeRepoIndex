"""
文档存储组件实现
负责存储和管理文本节点及其元数据
"""

import json
import os
from typing import List, Dict, Any, Optional
import logging

from .base import BaseDocumentStore
from .node import Node

logger = logging.getLogger(__name__)


class SimpleDocumentStore(BaseDocumentStore):
    """
    简单的文档存储实现
    基于内存字典存储，支持JSON持久化
    """
    
    def __init__(self, persist_path: Optional[str] = None):
        """
        初始化文档存储
        
        Args:
            persist_path: 持久化文件路径，如果提供则自动加载
        """
        # 核心存储：node_id -> Node
        self._nodes: Dict[str, Node] = {}
        
        # 如果提供了路径，尝试加载
        if persist_path and os.path.exists(persist_path):
            try:
                self.load_from_path(persist_path)
                logger.info(f"从 {persist_path} 加载了 {len(self._nodes)} 个节点")
            except Exception as e:
                logger.warning(f"无法从 {persist_path} 加载文档存储: {e}")
    
    def add_nodes(self, nodes: List[Node]) -> None:
        """
        添加节点到存储中
        
        Args:
            nodes: 节点列表
            
        Raises:
            ValueError: 如果节点ID已存在
        """
        for node in nodes:
            if node.node_id in self._nodes:
                logger.warning(f"节点 {node.node_id} 已存在，将被覆盖")
            
            self._nodes[node.node_id] = node
        
        logger.debug(f"添加了 {len(nodes)} 个节点，总数: {len(self._nodes)}")
    
    def add_node(self, node: Node) -> None:
        """
        添加单个节点
        
        Args:
            node: 节点对象
        """
        self.add_nodes([node])
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        根据ID获取单个节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点对象，如果不存在则返回None
        """
        return self._nodes.get(node_id)
    
    def get_nodes(self, node_ids: List[str]) -> List[Node]:
        """
        根据ID列表获取多个节点
        
        Args:
            node_ids: 节点ID列表
            
        Returns:
            节点列表，不存在的ID会被跳过
        """
        nodes = []
        for node_id in node_ids:
            node = self._nodes.get(node_id)
            if node:
                nodes.append(node)
            else:
                logger.warning(f"节点 {node_id} 不存在")
        
        return nodes
    
    def delete_node(self, node_id: str) -> bool:
        """
        删除指定节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否成功删除
        """
        if node_id in self._nodes:
            del self._nodes[node_id]
            logger.debug(f"删除节点 {node_id}")
            return True
        else:
            logger.warning(f"尝试删除不存在的节点 {node_id}")
            return False
    
    def delete_nodes(self, node_ids: List[str]) -> int:
        """
        批量删除节点
        
        Args:
            node_ids: 节点ID列表
            
        Returns:
            成功删除的节点数量
        """
        deleted_count = 0
        for node_id in node_ids:
            if self.delete_node(node_id):
                deleted_count += 1
        
        return deleted_count
    
    def get_all_node_ids(self) -> List[str]:
        """
        获取所有节点ID
        
        Returns:
            节点ID列表
        """
        return list(self._nodes.keys())
    
    def get_all_nodes(self) -> List[Node]:
        """
        获取所有节点
        
        Returns:
            节点列表
        """
        return list(self._nodes.values())
    
    def size(self) -> int:
        """
        获取存储的节点数量
        
        Returns:
            节点数量
        """
        return len(self._nodes)
    
    def clear(self) -> None:
        """清空所有节点"""
        self._nodes.clear()
        logger.info("清空了文档存储")
    
    def persist(self, filepath: str) -> None:
        """
        持久化到磁盘
        
        Args:
            filepath: 文件路径
            
        Raises:
            IOError: 如果写入失败
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 将节点转换为字典格式
            data = {
                'nodes': {
                    node_id: node.to_dict() 
                    for node_id, node in self._nodes.items()
                },
                'metadata': {
                    'total_nodes': len(self._nodes),
                    'version': '1.0'
                }
            }
            
            # 写入JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存 {len(self._nodes)} 个节点到 {filepath}")
            
        except Exception as e:
            logger.error(f"保存文档存储失败: {e}")
            raise IOError(f"无法保存到 {filepath}: {e}")
    
    def load_from_path(self, filepath: str) -> None:
        """
        从磁盘加载
        
        Args:
            filepath: 文件路径
            
        Raises:
            IOError: 如果读取失败
            ValueError: 如果数据格式错误
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据格式
            if 'nodes' not in data:
                raise ValueError("数据格式错误：缺少 'nodes' 字段")
            
            # 清空当前数据
            self._nodes.clear()
            
            # 加载节点
            nodes_data = data['nodes']
            for node_id, node_dict in nodes_data.items():
                try:
                    node = Node.from_dict(node_dict)
                    # 确保节点ID一致
                    node.node_id = node_id
                    self._nodes[node_id] = node
                except Exception as e:
                    logger.warning(f"跳过无效节点 {node_id}: {e}")
            
            logger.info(f"成功从 {filepath} 加载 {len(self._nodes)} 个节点")
            
        except FileNotFoundError:
            logger.warning(f"文件 {filepath} 不存在")
            raise IOError(f"文件不存在: {filepath}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise ValueError(f"无效的JSON格式: {e}")
        except Exception as e:
            logger.error(f"加载文档存储失败: {e}")
            raise IOError(f"无法从 {filepath} 加载: {e}")
    
    def update_node(self, node_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新节点信息
        
        Args:
            node_id: 节点ID
            updates: 更新的字段字典
            
        Returns:
            是否成功更新
        """
        if node_id not in self._nodes:
            logger.warning(f"节点 {node_id} 不存在，无法更新")
            return False
        
        node = self._nodes[node_id]
        
        # 更新支持的字段
        if 'text' in updates:
            node.text = updates['text']
        
        if 'metadata' in updates:
            # 合并元数据
            if isinstance(updates['metadata'], dict):
                node.metadata.update(updates['metadata'])
            else:
                node.metadata = updates['metadata']
        
        if 'relationships' in updates:
            if isinstance(updates['relationships'], dict):
                node.relationships.update(updates['relationships'])
            else:
                node.relationships = updates['relationships']
        
        logger.debug(f"更新节点 {node_id}")
        return True
    
    def search_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[Node]:
        """
        根据元数据搜索节点
        
        Args:
            metadata_filter: 元数据过滤条件
            
        Returns:
            匹配的节点列表
        """
        if not metadata_filter:
            return list(self._nodes.values())
        
        matching_nodes = []
        
        for node in self._nodes.values():
            match = True
            for key, value in metadata_filter.items():
                if key not in node.metadata or node.metadata[key] != value:
                    match = False
                    break
            
            if match:
                matching_nodes.append(node)
        
        return matching_nodes
    
    def search_metadata_contains(self, metadata_key: str, search_value: Any) -> List[Node]:
        """
        搜索元数据包含指定值的节点
        
        Args:
            metadata_key: 元数据键
            search_value: 搜索值
            
        Returns:
            匹配的节点列表
        """
        matching_nodes = []
        
        for node in self._nodes.values():
            if metadata_key in node.metadata:
                node_value = node.metadata[metadata_key]
                
                # 处理不同类型的包含检索
                if isinstance(node_value, str) and isinstance(search_value, str):
                    if search_value.lower() in node_value.lower():
                        matching_nodes.append(node)
                elif isinstance(node_value, list):
                    if search_value in node_value:
                        matching_nodes.append(node)
                elif node_value == search_value:
                    matching_nodes.append(node)
        
        return matching_nodes
    
    def search_metadata_range(self, metadata_key: str, min_value=None, max_value=None) -> List[Node]:
        """
        搜索元数据在指定范围内的节点
        
        Args:
            metadata_key: 元数据键
            min_value: 最小值（可选）
            max_value: 最大值（可选）
            
        Returns:
            匹配的节点列表
        """
        matching_nodes = []
        
        for node in self._nodes.values():
            if metadata_key in node.metadata:
                node_value = node.metadata[metadata_key]
                
                try:
                    # 尝试数值比较
                    if isinstance(node_value, (int, float)):
                        if min_value is not None and node_value < min_value:
                            continue
                        if max_value is not None and node_value > max_value:
                            continue
                        matching_nodes.append(node)
                    # 字符串比较
                    elif isinstance(node_value, str):
                        if min_value is not None and node_value < str(min_value):
                            continue
                        if max_value is not None and node_value > str(max_value):
                            continue
                        matching_nodes.append(node)
                except (TypeError, ValueError):
                    # 无法比较的类型，跳过
                    continue
        
        return matching_nodes
    
    def search_metadata_exists(self, metadata_keys: List[str], require_all: bool = True) -> List[Node]:
        """
        搜索包含指定元数据键的节点
        
        Args:
            metadata_keys: 元数据键列表
            require_all: 是否要求包含所有键（True）还是任意一个键（False）
            
        Returns:
            匹配的节点列表
        """
        matching_nodes = []
        
        for node in self._nodes.values():
            if require_all:
                # 要求包含所有键
                if all(key in node.metadata for key in metadata_keys):
                    matching_nodes.append(node)
            else:
                # 只要包含任意一个键
                if any(key in node.metadata for key in metadata_keys):
                    matching_nodes.append(node)
        
        return matching_nodes
    
    def get_metadata_values(self, metadata_key: str) -> List[Any]:
        """
        获取指定元数据键的所有唯一值
        
        Args:
            metadata_key: 元数据键
            
        Returns:
            唯一值列表
        """
        values = set()
        
        for node in self._nodes.values():
            if metadata_key in node.metadata:
                value = node.metadata[metadata_key]
                if isinstance(value, list):
                    values.update(value)
                else:
                    values.add(value)
        
        return list(values)
    
    def get_metadata_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        获取元数据统计信息
        
        Returns:
            元数据统计字典
        """
        metadata_stats = {}
        
        # 收集所有元数据键
        all_keys = set()
        for node in self._nodes.values():
            all_keys.update(node.metadata.keys())
        
        # 为每个键计算统计信息
        for key in all_keys:
            values = []
            for node in self._nodes.values():
                if key in node.metadata:
                    values.append(node.metadata[key])
            
            stats = {
                'count': len(values),
                'unique_values': len(set(str(v) for v in values)),
                'coverage': len(values) / len(self._nodes) if self._nodes else 0
            }
            
            # 如果是数值类型，添加更多统计
            numeric_values = []
            for v in values:
                if isinstance(v, (int, float)):
                    numeric_values.append(v)
            
            if numeric_values:
                stats.update({
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'avg': sum(numeric_values) / len(numeric_values)
                })
            
            metadata_stats[key] = stats
        
        return metadata_stats
    
    def get_nodes_by_doc_id(self, doc_id: str) -> List[Node]:
        """
        根据文档ID获取所有相关节点
        
        Args:
            doc_id: 文档ID
            
        Returns:
            属于该文档的节点列表
        """
        return self.search_by_metadata({'doc_id': doc_id})
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        if not self._nodes:
            return {
                'total_nodes': 0,
                'total_text_length': 0,
                'average_text_length': 0,
                'doc_ids': []
            }
        
        total_text_length = sum(len(node.text) for node in self._nodes.values())
        doc_ids = set()
        
        for node in self._nodes.values():
            if 'doc_id' in node.metadata:
                doc_ids.add(node.metadata['doc_id'])
        
        return {
            'total_nodes': len(self._nodes),
            'total_text_length': total_text_length,
            'average_text_length': total_text_length / len(self._nodes),
            'unique_docs': len(doc_ids),
            'doc_ids': list(doc_ids)
        }
    
    def __len__(self) -> int:
        """返回节点数量"""
        return len(self._nodes)
    
    def __contains__(self, node_id: str) -> bool:
        """检查节点是否存在"""
        return node_id in self._nodes
    
    def __iter__(self):
        """迭代所有节点"""
        return iter(self._nodes.values())


def create_document_store(
    store_type: str = "simple", 
    persist_path: Optional[str] = None,
    **kwargs
) -> BaseDocumentStore:
    """
    创建文档存储实例
    
    Args:
        store_type: 存储类型，目前只支持 "simple"
        persist_path: 持久化路径
        **kwargs: 其他参数
        
    Returns:
        文档存储实例
        
    Raises:
        ValueError: 如果存储类型不支持
    """
    if store_type == "simple":
        return SimpleDocumentStore(persist_path=persist_path, **kwargs)
    else:
        raise ValueError(f"不支持的文档存储类型: {store_type}") 