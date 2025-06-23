# coding: utf-8
"""
C++代码解析器测试模块
测试C++语言的代码解析功能
"""

import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class CppParserTester:
    """C++解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_cpp_test_file(self) -> Path:
        """创建C++测试文件"""
        cpp_code = '''/*
 * C++测试文件
 * 包含类、模板、STL容器、智能指针等C++特性
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <algorithm>
#include <functional>
#include <thread>
#include <mutex>

using namespace std;

// 前向声明
class User;
template<typename T> class Repository;

// 枚举类
enum class UserRole {
    Admin,
    User,
    Guest
};

// 用户基类
class BaseEntity {
protected:
    int id_;
    string created_at_;

public:
    BaseEntity(int id) : id_(id), created_at_(getCurrentTime()) {}
    
    virtual ~BaseEntity() = default;
    
    // 纯虚函数
    virtual bool validate() const = 0;
    
    // 虚函数
    virtual string toString() const {
        return "BaseEntity[id=" + to_string(id_) + "]";
    }
    
    // Getter
    int getId() const { return id_; }
    const string& getCreatedAt() const { return created_at_; }

private:
    string getCurrentTime() const {
        return "2024-01-01 00:00:00";
    }
};

// 用户类
class User : public BaseEntity {
private:
    string name_;
    string email_;
    UserRole role_;
    vector<string> permissions_;
    mutable mutex mutex_;

public:
    // 构造函数
    User(int id, const string& name, const string& email, UserRole role)
        : BaseEntity(id), name_(name), email_(email), role_(role) {}
    
    // 拷贝构造函数
    User(const User& other) : BaseEntity(other.id_) {
        lock_guard<mutex> lock(other.mutex_);
        name_ = other.name_;
        email_ = other.email_;
        role_ = other.role_;
        permissions_ = other.permissions_;
    }
    
    // 移动构造函数
    User(User&& other) noexcept : BaseEntity(other.id_) {
        lock_guard<mutex> lock(other.mutex_);
        name_ = move(other.name_);
        email_ = move(other.email_);
        role_ = other.role_;
        permissions_ = move(other.permissions_);
    }
    
    // 拷贝赋值操作符
    User& operator=(const User& other) {
        if (this != &other) {
            lock(mutex_, other.mutex_);
            lock_guard<mutex> lock1(mutex_, adopt_lock);
            lock_guard<mutex> lock2(other.mutex_, adopt_lock);
            
            name_ = other.name_;
            email_ = other.email_;
            role_ = other.role_;
            permissions_ = other.permissions_;
        }
        return *this;
    }
    
    // 移动赋值操作符
    User& operator=(User&& other) noexcept {
        if (this != &other) {
            lock(mutex_, other.mutex_);
            lock_guard<mutex> lock1(mutex_, adopt_lock);
            lock_guard<mutex> lock2(other.mutex_, adopt_lock);
            
            name_ = move(other.name_);
            email_ = move(other.email_);
            role_ = other.role_;
            permissions_ = move(other.permissions_);
        }
        return *this;
    }
    
    // 重写基类方法
    bool validate() const override {
        lock_guard<mutex> lock(mutex_);
        return !name_.empty() && email_.find('@') != string::npos;
    }
    
    string toString() const override {
        lock_guard<mutex> lock(mutex_);
        return "User[id=" + to_string(id_) + ", name=" + name_ + "]";
    }
    
    // 业务方法
    void addPermission(const string& permission) {
        lock_guard<mutex> lock(mutex_);
        auto it = find(permissions_.begin(), permissions_.end(), permission);
        if (it == permissions_.end()) {
            permissions_.push_back(permission);
        }
    }
    
    bool hasPermission(const string& permission) const {
        lock_guard<mutex> lock(mutex_);
        return find(permissions_.begin(), permissions_.end(), permission) != permissions_.end();
    }
    
    // 静态方法
    static unique_ptr<User> createAdmin(int id, const string& name, const string& email) {
        auto user = make_unique<User>(id, name, email, UserRole::Admin);
        user->addPermission("READ");
        user->addPermission("WRITE");
        user->addPermission("DELETE");
        return user;
    }
    
    // Getters
    const string& getName() const { 
        lock_guard<mutex> lock(mutex_);
        return name_; 
    }
    
    const string& getEmail() const { 
        lock_guard<mutex> lock(mutex_);
        return email_; 
    }
    
    UserRole getRole() const { 
        lock_guard<mutex> lock(mutex_);
        return role_; 
    }
    
    vector<string> getPermissions() const {
        lock_guard<mutex> lock(mutex_);
        return permissions_;
    }
};

// 模板类 - 泛型仓库
template<typename T, typename Key = int>
class Repository {
private:
    map<Key, shared_ptr<T>> storage_;
    mutable mutex mutex_;

public:
    // 查找元素
    shared_ptr<T> findById(const Key& id) const {
        lock_guard<mutex> lock(mutex_);
        auto it = storage_.find(id);
        return (it != storage_.end()) ? it->second : nullptr;
    }
    
    // 获取所有元素
    vector<shared_ptr<T>> findAll() const {
        lock_guard<mutex> lock(mutex_);
        vector<shared_ptr<T>> result;
        for (const auto& pair : storage_) {
            result.push_back(pair.second);
        }
        return result;
    }
    
    // 保存元素
    void save(const Key& id, shared_ptr<T> entity) {
        lock_guard<mutex> lock(mutex_);
        storage_[id] = entity;
    }
    
    // 删除元素
    bool remove(const Key& id) {
        lock_guard<mutex> lock(mutex_);
        return storage_.erase(id) > 0;
    }
    
    // 获取数量
    size_t size() const {
        lock_guard<mutex> lock(mutex_);
        return storage_.size();
    }
    
    // 模板成员函数
    template<typename Predicate>
    vector<shared_ptr<T>> findWhere(Predicate pred) const {
        lock_guard<mutex> lock(mutex_);
        vector<shared_ptr<T>> result;
        for (const auto& pair : storage_) {
            if (pred(*pair.second)) {
                result.push_back(pair.second);
            }
        }
        return result;
    }
};

// 服务类
class UserService {
private:
    unique_ptr<Repository<User>> repository_;
    
public:
    UserService() : repository_(make_unique<Repository<User>>()) {}
    
    ~UserService() = default;
    
    // 不允许拷贝
    UserService(const UserService&) = delete;
    UserService& operator=(const UserService&) = delete;
    
    // 允许移动
    UserService(UserService&&) = default;
    UserService& operator=(UserService&&) = default;
    
    // 创建用户
    shared_ptr<User> createUser(int id, const string& name, const string& email, UserRole role) {
        auto user = make_shared<User>(id, name, email, role);
        if (user->validate()) {
            repository_->save(id, user);
            return user;
        }
        throw invalid_argument("Invalid user data");
    }
    
    // 获取用户
    shared_ptr<User> getUser(int id) const {
        return repository_->findById(id);
    }
    
    // 获取所有用户
    vector<shared_ptr<User>> getAllUsers() const {
        return repository_->findAll();
    }
    
    // 根据角色查找用户
    vector<shared_ptr<User>> getUsersByRole(UserRole role) const {
        return repository_->findWhere([role](const User& user) {
            return user.getRole() == role;
        });
    }
    
    // 删除用户
    bool deleteUser(int id) {
        return repository_->remove(id);
    }
};

// 函数模板
template<typename Container, typename Predicate>
auto filterContainer(const Container& container, Predicate pred) -> vector<typename Container::value_type> {
    vector<typename Container::value_type> result;
    copy_if(container.begin(), container.end(), back_inserter(result), pred);
    return result;
}

// 特化模板
template<>
class Repository<User, string> {
private:
    map<string, shared_ptr<User>> storage_;
    
public:
    void save(const string& email, shared_ptr<User> user) {
        storage_[email] = user;
    }
    
    shared_ptr<User> findByEmail(const string& email) const {
        auto it = storage_.find(email);
        return (it != storage_.end()) ? it->second : nullptr;
    }
};

// Lambda 和现代C++特性示例
class ModernCppExample {
public:
    // 使用auto和lambda
    auto processUsers(const vector<shared_ptr<User>>& users) {
        return [users](const string& permission) {
            vector<shared_ptr<User>> result;
            copy_if(users.begin(), users.end(), back_inserter(result),
                   [&permission](const shared_ptr<User>& user) {
                       return user->hasPermission(permission);
                   });
            return result;
        };
    }
    
    // 使用智能指针和RAII
    unique_ptr<UserService> createUserService() {
        return make_unique<UserService>();
    }
    
    // 范围for循环
    void printUsers(const vector<shared_ptr<User>>& users) {
        for (const auto& user : users) {
            cout << user->toString() << endl;
        }
    }
};

// 工具函数
namespace UserUtils {
    string roleToString(UserRole role) {
        switch (role) {
            case UserRole::Admin: return "Admin";
            case UserRole::User: return "User";
            case UserRole::Guest: return "Guest";
            default: return "Unknown";
        }
    }
    
    UserRole stringToRole(const string& roleStr) {
        if (roleStr == "Admin") return UserRole::Admin;
        if (roleStr == "User") return UserRole::User;
        if (roleStr == "Guest") return UserRole::Guest;
        throw invalid_argument("Invalid role string: " + roleStr);
    }
}

// 主函数
int main() {
    cout << "C++ Parser Test Program" << endl;
    cout << "======================" << endl;
    
    try {
        // 创建服务
        auto userService = make_unique<UserService>();
        
        // 创建用户
        auto admin = userService->createUser(1, "管理员", "admin@example.com", UserRole::Admin);
        auto user = userService->createUser(2, "普通用户", "user@example.com", UserRole::User);
        
        // 输出用户信息
        cout << "Created users:" << endl;
        cout << admin->toString() << endl;
        cout << user->toString() << endl;
        
        // 使用现代C++特性
        ModernCppExample example;
        auto users = userService->getAllUsers();
        example.printUsers(users);
        
        // 使用lambda过滤
        auto processor = example.processUsers(users);
        auto admins = processor("READ");
        
        cout << "Admin users count: " << admins.size() << endl;
        
    } catch (const exception& e) {
        cerr << "Error: " << e.what() << endl;
        return 1;
    }
    
    return 0;
}
'''
        
        temp_file = Path(tempfile.mktemp(suffix=".cpp"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(cpp_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_cpp_parsing(self):
        """测试C++解析功能"""
        logger.info("开始C++解析测试")
        print("=== C++解析测试 ===")
        
        test_file = self.create_cpp_test_file()
        result = self.parser.parse_file(str(test_file))
        
        print(f"语言: {result.language.value if result.language else 'Unknown'}")
        print(f"代码片段数量: {len(result.snippets)}")
        print(f"处理时间: {result.processing_time:.4f}s")
        print(f"是否成功: {result.is_successful}")
        
        if result.errors:
            print(f"错误信息: {result.errors}")
        
        # 分析代码片段
        classes = [s for s in result.snippets if s.type == 'class']
        functions = [s for s in result.snippets if s.type in ['function', 'method']]
        
        print(f"\n发现的类: {len(classes)}")
        for cls in classes[:5]:
            print(f"  - {cls.name} (行 {cls.line_start}-{cls.line_end})")
        
        print(f"\n发现的函数/方法: {len(functions)}")
        for func in functions[:8]:
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{func.line_end})")
        
        logger.success("C++解析测试完成")
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
        """运行C++解析测试"""
        try:
            result = self.test_cpp_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = CppParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 