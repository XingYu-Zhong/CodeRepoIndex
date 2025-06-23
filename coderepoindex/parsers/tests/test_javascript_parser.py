# coding: utf-8
"""
JavaScript代码解析器测试模块
测试JavaScript语言的代码解析功能
"""

import tempfile
from pathlib import Path
from typing import List
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class JavaScriptParserTester:
    """JavaScript解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_javascript_test_file(self) -> Path:
        """创建JavaScript测试文件"""
        javascript_code = '''/**
 * JavaScript/ES6+ 测试文件
 * 包含类、函数、箭头函数、异步函数等现代JavaScript特性
 * @author Test Author
 * @version 1.0.0
 */

// 导入模块
import React, { Component, useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import axios from 'axios';
import _ from 'lodash';

// 常量定义
const API_BASE_URL = 'https://api.example.com';
const MAX_RETRY_COUNT = 3;
const DEFAULT_TIMEOUT = 5000;

// 配置对象
const config = {
    environment: 'development',
    debug: true,
    features: {
        enableAuth: true,
        enableLogging: true,
        enableAnalytics: false
    }
};

/**
 * 工具函数集合
 */
const Utils = {
    /**
     * 深拷贝对象
     * @param {Object} obj - 要拷贝的对象
     * @returns {Object} 拷贝后的对象
     */
    deepClone: (obj) => {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj);
        if (obj instanceof Array) return obj.map(item => Utils.deepClone(item));
        
        const cloned = {};
        for (let key in obj) {
            if (obj.hasOwnProperty(key)) {
                cloned[key] = Utils.deepClone(obj[key]);
            }
        }
        return cloned;
    },

    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} delay - 延迟时间
     * @returns {Function} 防抖后的函数
     */
    debounce: (func, delay) => {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 限制时间
     * @returns {Function} 节流后的函数
     */
    throttle: (func, limit) => {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

/**
 * 用户类
 */
class User {
    /**
     * 构造函数
     * @param {string} name - 用户名
     * @param {string} email - 邮箱
     * @param {number} age - 年龄
     */
    constructor(name, email, age) {
        this.name = name;
        this.email = email;
        this.age = age;
        this.createdAt = new Date();
        this.permissions = [];
    }

    /**
     * 获取用户信息
     * @returns {Object} 用户信息对象
     */
    getInfo() {
        return {
            name: this.name,
            email: this.email,
            age: this.age,
            memberSince: this.createdAt
        };
    }

    /**
     * 添加权限
     * @param {string} permission - 权限名称
     */
    addPermission(permission) {
        if (!this.permissions.includes(permission)) {
            this.permissions.push(permission);
        }
    }

    /**
     * 检查权限
     * @param {string} permission - 权限名称
     * @returns {boolean} 是否有权限
     */
    hasPermission(permission) {
        return this.permissions.includes(permission);
    }

    /**
     * 静态方法：创建管理员用户
     * @param {string} name - 用户名
     * @param {string} email - 邮箱
     * @returns {User} 管理员用户实例
     */
    static createAdmin(name, email) {
        const admin = new User(name, email, 0);
        admin.addPermission('admin');
        admin.addPermission('read');
        admin.addPermission('write');
        return admin;
    }

    /**
     * 获取用户显示名称
     */
    get displayName() {
        return `${this.name} <${this.email}>`;
    }

    /**
     * 设置用户年龄
     */
    set userAge(age) {
        if (age >= 0 && age <= 120) {
            this.age = age;
        } else {
            throw new Error('年龄必须在0-120之间');
        }
    }
}

/**
 * 高级用户类（继承自User）
 */
class PremiumUser extends User {
    constructor(name, email, age, subscriptionType = 'basic') {
        super(name, email, age);
        this.subscriptionType = subscriptionType;
        this.subscriptionDate = new Date();
    }

    /**
     * 升级订阅
     * @param {string} newType - 新的订阅类型
     */
    upgradeSubscription(newType) {
        const validTypes = ['basic', 'premium', 'enterprise'];
        if (validTypes.includes(newType)) {
            this.subscriptionType = newType;
            console.log(`订阅已升级至 ${newType}`);
        }
    }

    /**
     * 获取订阅信息
     * @returns {Object} 订阅信息
     */
    getSubscriptionInfo() {
        return {
            ...super.getInfo(),
            subscriptionType: this.subscriptionType,
            subscriptionDate: this.subscriptionDate
        };
    }
}

/**
 * API服务类
 */
class ApiService {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
        this.timeout = DEFAULT_TIMEOUT;
        this.retryCount = MAX_RETRY_COUNT;
    }

    /**
     * 发送GET请求
     * @param {string} endpoint - API端点
     * @param {Object} params - 查询参数
     * @returns {Promise} 响应数据
     */
    async get(endpoint, params = {}) {
        try {
            const url = new URL(endpoint, this.baseURL);
            Object.keys(params).forEach(key => 
                url.searchParams.append(key, params[key])
            );

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout: this.timeout
            });

            if (!response.ok) {
                throw new Error(`HTTP错误! 状态: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('GET请求失败:', error);
            throw error;
        }
    }

    /**
     * 发送POST请求
     * @param {string} endpoint - API端点
     * @param {Object} data - 请求数据
     * @returns {Promise} 响应数据
     */
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data),
                timeout: this.timeout
            });

            return await response.json();
        } catch (error) {
            console.error('POST请求失败:', error);
            throw error;
        }
    }

    /**
     * 带重试的请求
     * @param {Function} requestFunc - 请求函数
     * @param {number} maxRetries - 最大重试次数
     * @returns {Promise} 响应数据
     */
    async requestWithRetry(requestFunc, maxRetries = this.retryCount) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await requestFunc();
            } catch (error) {
                if (i === maxRetries - 1) throw error;
                
                const delay = Math.pow(2, i) * 1000; // 指数退避
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
}

/**
 * React组件示例
 */
const UserProfile = ({ userId }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 使用useEffect钩子
    useEffect(() => {
        const fetchUser = async () => {
            try {
                setLoading(true);
                const apiService = new ApiService();
                const userData = await apiService.get(`/users/${userId}`);
                setUser(userData);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (userId) {
            fetchUser();
        }
    }, [userId]);

    if (loading) return <div>加载中...</div>;
    if (error) return <div>错误: {error}</div>;
    if (!user) return <div>未找到用户</div>;

    return (
        <div className="user-profile">
            <h2>{user.name}</h2>
            <p>邮箱: {user.email}</p>
            <p>年龄: {user.age}</p>
        </div>
    );
};

/**
 * React类组件示例
 */
class TodoList extends Component {
    constructor(props) {
        super(props);
        this.state = {
            todos: [],
            inputValue: '',
            filter: 'all'
        };
    }

    /**
     * 组件挂载后
     */
    componentDidMount() {
        this.loadTodos();
    }

    /**
     * 加载待办事项
     */
    loadTodos = async () => {
        try {
            const apiService = new ApiService();
            const todos = await apiService.get('/todos');
            this.setState({ todos });
        } catch (error) {
            console.error('加载待办事项失败:', error);
        }
    }

    /**
     * 添加待办事项
     */
    addTodo = () => {
        const { inputValue, todos } = this.state;
        if (inputValue.trim()) {
            const newTodo = {
                id: Date.now(),
                text: inputValue,
                completed: false,
                createdAt: new Date()
            };
            this.setState({
                todos: [...todos, newTodo],
                inputValue: ''
            });
        }
    }

    /**
     * 切换待办事项状态
     * @param {number} id - 待办事项ID
     */
    toggleTodo = (id) => {
        this.setState(prevState => ({
            todos: prevState.todos.map(todo =>
                todo.id === id ? { ...todo, completed: !todo.completed } : todo
            )
        }));
    }

    /**
     * 删除待办事项
     * @param {number} id - 待办事项ID
     */
    deleteTodo = (id) => {
        this.setState(prevState => ({
            todos: prevState.todos.filter(todo => todo.id !== id)
        }));
    }

    render() {
        const { todos, inputValue, filter } = this.state;
        
        const filteredTodos = todos.filter(todo => {
            if (filter === 'completed') return todo.completed;
            if (filter === 'active') return !todo.completed;
            return true;
        });

        return (
            <div className="todo-list">
                <h1>待办事项</h1>
                <div className="todo-input">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => this.setState({ inputValue: e.target.value })}
                        onKeyPress={(e) => e.key === 'Enter' && this.addTodo()}
                        placeholder="添加新的待办事项..."
                    />
                    <button onClick={this.addTodo}>添加</button>
                </div>
                <div className="todo-items">
                    {filteredTodos.map(todo => (
                        <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
                            <input
                                type="checkbox"
                                checked={todo.completed}
                                onChange={() => this.toggleTodo(todo.id)}
                            />
                            <span>{todo.text}</span>
                            <button onClick={() => this.deleteTodo(todo.id)}>删除</button>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
}

// 箭头函数示例
const calculateSum = (numbers) => numbers.reduce((sum, num) => sum + num, 0);

const findMax = (numbers) => Math.max(...numbers);

const filterEven = (numbers) => numbers.filter(num => num % 2 === 0);

// 高阶函数示例
const createMultiplier = (factor) => (number) => number * factor;

const double = createMultiplier(2);
const triple = createMultiplier(3);

// 异步函数示例
async function processDataBatch(dataList) {
    const results = [];
    
    for (const data of dataList) {
        try {
            const processed = await processData(data);
            results.push(processed);
        } catch (error) {
            console.error('处理数据失败:', error);
            results.push(null);
        }
    }
    
    return results;
}

// Promise示例
function processData(data) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (data && typeof data === 'object') {
                resolve({
                    ...data,
                    processed: true,
                    timestamp: Date.now()
                });
            } else {
                reject(new Error('无效的数据格式'));
            }
        }, Math.random() * 100);
    });
}

// 生成器函数
function* fibonacci(limit) {
    let a = 0, b = 1;
    while (a < limit) {
        yield a;
        [a, b] = [b, a + b];
    }
}

// 模块导出
export {
    User,
    PremiumUser,
    ApiService,
    UserProfile,
    TodoList,
    Utils,
    calculateSum,
    findMax,
    filterEven,
    processDataBatch,
    fibonacci
};

export default {
    User,
    ApiService,
    Utils
};

// 立即执行函数表达式 (IIFE)
(function() {
    console.log('JavaScript解析器测试文件已加载');
})();
'''
        
        # 创建临时文件
        temp_file = Path(tempfile.mktemp(suffix=".js"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(javascript_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_javascript_parsing(self):
        """测试JavaScript解析功能"""
        logger.info("开始JavaScript解析测试")
        print("=== JavaScript解析测试 ===")
        
        test_file = self.create_javascript_test_file()
        logger.info(f"创建测试文件: {test_file}")
        
        # 解析文件
        result = self.parser.parse_file(str(test_file))
        
        # 验证结果
        print(f"语言: {result.language.value if result.language else 'Unknown'}")
        print(f"文件路径: {result.file_path}")
        print(f"代码片段数量: {len(result.snippets)}")
        print(f"处理时间: {result.processing_time:.4f}s")
        print(f"是否成功: {result.is_successful}")
        
        if result.errors:
            print(f"错误信息: {result.errors}")
        
        # 分析代码片段
        classes = [s for s in result.snippets if s.type == 'class']
        functions = [s for s in result.snippets if s.type in ['function', 'method']]
        
        print(f"\n发现的类: {len(classes)}")
        for cls in classes:
            print(f"  - {cls.name} (行 {cls.line_start}-{cls.line_end})")
        
        print(f"\n发现的函数/方法: {len(functions)}")
        for func in functions[:10]:  # 只显示前10个
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{func.line_end})")
            if func.class_name:
                print(f"    所属类: {func.class_name}")
        
        logger.success("JavaScript解析测试完成")
        return result
    
    def cleanup_test_files(self):
        """清理测试文件"""
        for file_path in self.test_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.error(f"清理文件失败: {file_path}, 错误: {e}")
    
    def run_test(self):
        """运行JavaScript解析测试"""
        try:
            result = self.test_javascript_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = JavaScriptParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 