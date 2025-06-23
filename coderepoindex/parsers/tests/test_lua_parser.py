# coding: utf-8
"""
Lua代码解析器测试模块
测试Lua语言的代码解析功能
"""

import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class LuaParserTester:
    """Lua解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_lua_test_file(self) -> Path:
        """创建Lua测试文件"""
        lua_code = '''--[[
Lua测试文件
包含函数、表、元表、协程等Lua特性
--]]

-- 模块定义
local UserModule = {}

-- 常量定义
local USER_ROLES = {
    ADMIN = "admin",
    USER = "user", 
    GUEST = "guest"
}

local MAX_USERS = 1000
local VERSION = "1.0.0"

-- 用户类定义
local User = {}
User.__index = User

-- 构造函数
function User:new(id, name, email, role)
    local user = {
        id = id or 0,
        name = name or "",
        email = email or "",
        role = role or USER_ROLES.GUEST,
        permissions = {},
        created_at = os.time(),
        is_active = true
    }
    setmetatable(user, self)
    return user
end

-- 验证用户数据
function User:validate()
    if not self.name or self.name == "" then
        return false, "用户名不能为空"
    end
    
    if not self.email or not string.find(self.email, "@") then
        return false, "邮箱格式不正确"
    end
    
    local valid_roles = {
        [USER_ROLES.ADMIN] = true,
        [USER_ROLES.USER] = true,
        [USER_ROLES.GUEST] = true
    }
    
    if not valid_roles[self.role] then
        return false, "用户角色无效"
    end
    
    return true, nil
end

-- 添加权限
function User:addPermission(permission)
    if not self:hasPermission(permission) then
        table.insert(self.permissions, permission)
    end
end

-- 检查权限
function User:hasPermission(permission)
    for _, perm in ipairs(self.permissions) do
        if perm == permission then
            return true
        end
    end
    return false
end

-- 获取用户信息
function User:getInfo()
    return {
        id = self.id,
        name = self.name,
        email = self.email,
        role = self.role,
        permissions = self.permissions,
        created_at = self.created_at,
        is_active = self.is_active
    }
end

-- 设置用户状态
function User:setActive(active)
    self.is_active = active
end

-- 获取显示名称
function User:getDisplayName()
    local role_names = {
        [USER_ROLES.ADMIN] = "管理员",
        [USER_ROLES.USER] = "普通用户",
        [USER_ROLES.GUEST] = "访客"
    }
    return self.name .. " (" .. (role_names[self.role] or "未知") .. ")"
end

-- 静态方法：创建管理员
function User.createAdmin(name, email)
    local admin = User:new(os.time(), name, email, USER_ROLES.ADMIN)
    admin:addPermission("READ")
    admin:addPermission("WRITE")
    admin:addPermission("DELETE")
    admin:addPermission("ADMIN")
    return admin
end

-- 用户仓库
local UserRepository = {}
UserRepository.__index = UserRepository

function UserRepository:new()
    local repo = {
        users = {},
        next_id = 1
    }
    setmetatable(repo, self)
    return repo
end

-- 保存用户
function UserRepository:save(user)
    if not user.id or user.id == 0 then
        user.id = self.next_id
        self.next_id = self.next_id + 1
    end
    
    local is_valid, error_msg = user:validate()
    if not is_valid then
        return nil, error_msg
    end
    
    self.users[user.id] = user
    return user, nil
end

-- 根据ID查找用户
function UserRepository:findById(id)
    return self.users[id]
end

-- 获取所有用户
function UserRepository:findAll()
    local all_users = {}
    for _, user in pairs(self.users) do
        table.insert(all_users, user)
    end
    return all_users
end

-- 根据角色查找用户
function UserRepository:findByRole(role)
    local users_by_role = {}
    for _, user in pairs(self.users) do
        if user.role == role then
            table.insert(users_by_role, user)
        end
    end
    return users_by_role
end

-- 删除用户
function UserRepository:delete(id)
    if self.users[id] then
        self.users[id] = nil
        return true
    end
    return false
end

-- 获取用户数量
function UserRepository:count()
    local count = 0
    for _ in pairs(self.users) do
        count = count + 1
    end
    return count
end

-- 用户服务
local UserService = {}
UserService.__index = UserService

function UserService:new(repository)
    local service = {
        repository = repository or UserRepository:new()
    }
    setmetatable(service, self)
    return service
end

-- 创建用户
function UserService:createUser(name, email, role)
    local user = User:new(nil, name, email, role)
    local saved_user, error_msg = self.repository:save(user)
    if saved_user then
        return saved_user, nil
    else
        return nil, error_msg
    end
end

-- 获取用户
function UserService:getUser(id)
    local user = self.repository:findById(id)
    if user then
        return user, nil
    else
        return nil, "用户不存在"
    end
end

-- 更新用户
function UserService:updateUser(id, updates)
    local user = self.repository:findById(id)
    if not user then
        return nil, "用户不存在"
    end
    
    -- 更新字段
    for key, value in pairs(updates) do
        if key ~= "id" then  -- 不允许更新ID
            user[key] = value
        end
    end
    
    local saved_user, error_msg = self.repository:save(user)
    return saved_user, error_msg
end

-- 删除用户
function UserService:deleteUser(id)
    return self.repository:delete(id)
end

-- 获取所有用户
function UserService:getAllUsers()
    return self.repository:findAll()
end

-- 批量处理用户
function UserService:processUsersBatch(processor)
    local users = self.repository:findAll()
    for _, user in ipairs(users) do
        processor(user)
    end
end

-- 工具函数
local Utils = {}

-- 表的深拷贝
function Utils.deepCopy(original)
    local copy
    if type(original) == "table" then
        copy = {}
        for key, value in next, original, nil do
            copy[Utils.deepCopy(key)] = Utils.deepCopy(value)
        end
        setmetatable(copy, Utils.deepCopy(getmetatable(original)))
    else
        copy = original
    end
    return copy
end

-- 检查表是否为空
function Utils.isEmpty(table)
    return next(table) == nil
end

-- 获取表的长度（包括非数组部分）
function Utils.tableLength(table)
    local count = 0
    for _ in pairs(table) do
        count = count + 1
    end
    return count
end

-- 合并两个表
function Utils.mergeTables(table1, table2)
    local result = Utils.deepCopy(table1)
    for key, value in pairs(table2) do
        result[key] = value
    end
    return result
end

-- 过滤表
function Utils.filter(table, predicate)
    local result = {}
    for _, value in ipairs(table) do
        if predicate(value) then
            table.insert(result, value)
        end
    end
    return result
end

-- 映射表
function Utils.map(table, mapper)
    local result = {}
    for _, value in ipairs(table) do
        table.insert(result, mapper(value))
    end
    return result
end

-- 协程示例
function UserService:processUsersAsync(callback)
    local co = coroutine.create(function()
        local users = self.repository:findAll()
        for i, user in ipairs(users) do
            coroutine.yield(user, i, #users)
        end
    end)
    
    return function()
        local status, user, index, total = coroutine.resume(co)
        if status and user then
            if callback then
                callback(user, index, total)
            end
            return user, index, total
        end
        return nil
    end
end

-- 元表示例
local ReadOnlyTable = {}

function ReadOnlyTable.new(table)
    local proxy = {}
    setmetatable(proxy, {
        __index = table,
        __newindex = function()
            error("尝试修改只读表")
        end
    })
    return proxy
end

-- 闭包示例
function createCounter(initial)
    local count = initial or 0
    return function(increment)
        count = count + (increment or 1)
        return count
    end
end

-- 错误处理包装器
function Utils.safeCall(func, ...)
    local status, result = pcall(func, ...)
    if status then
        return result, nil
    else
        return nil, result
    end
end

-- 模块导出
UserModule.User = User
UserModule.UserRepository = UserRepository
UserModule.UserService = UserService
UserModule.Utils = Utils
UserModule.USER_ROLES = USER_ROLES
UserModule.ReadOnlyTable = ReadOnlyTable
UserModule.createCounter = createCounter

-- 主函数
function UserModule.main()
    print("Lua Parser Test Program")
    print("=======================")
    
    -- 创建仓库和服务
    local repository = UserRepository:new()
    local userService = UserService:new(repository)
    
    -- 创建用户
    local admin, admin_error = userService:createUser("管理员", "admin@example.com", USER_ROLES.ADMIN)
    if admin then
        print("创建管理员成功:", admin:getDisplayName())
        admin:addPermission("READ")
        admin:addPermission("WRITE")
        admin:addPermission("DELETE")
    else
        print("创建管理员失败:", admin_error)
    end
    
    local user, user_error = userService:createUser("普通用户", "user@example.com", USER_ROLES.USER)
    if user then
        print("创建用户成功:", user:getDisplayName())
        user:addPermission("READ")
    else
        print("创建用户失败:", user_error)
    end
    
    -- 测试协程
    local iterator = userService:processUsersAsync(function(user, index, total)
        print(string.format("处理用户 %d/%d: %s", index, total, user.name))
    end)
    
    while true do
        local user, index, total = iterator()
        if not user then break end
    end
    
    -- 测试工具函数
    local counter = createCounter(10)
    print("计数器:", counter(5)) -- 15
    print("计数器:", counter(3)) -- 18
    
    -- 测试只读表
    local readonly_config = ReadOnlyTable.new({
        version = VERSION,
        max_users = MAX_USERS
    })
    
    print("配置版本:", readonly_config.version)
    
    -- 测试安全调用
    local result, error = Utils.safeCall(function()
        return 10 / 2
    end)
    print("安全调用结果:", result, error)
    
    print("测试完成")
end

-- 如果作为主文件运行
if arg and arg[0] == "test_lua_file.lua" then
    UserModule.main()
end

return UserModule
'''
        
        temp_file = Path(tempfile.mktemp(suffix=".lua"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(lua_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_lua_parsing(self):
        """测试Lua解析功能"""
        logger.info("开始Lua解析测试")
        print("=== Lua解析测试 ===")
        
        test_file = self.create_lua_test_file()
        result = self.parser.parse_file(str(test_file))
        
        print(f"语言: {result.language.value if result.language else 'Unknown'}")
        print(f"代码片段数量: {len(result.snippets)}")
        print(f"处理时间: {result.processing_time:.4f}s")
        print(f"是否成功: {result.is_successful}")
        
        if result.errors:
            print(f"错误信息: {result.errors}")
        
        # 分析代码片段
        functions = [s for s in result.snippets if s.type in ['function', 'method']]
        
        print(f"\n发现的函数: {len(functions)}")
        for func in functions[:10]:
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{func.line_end})")
        
        logger.success("Lua解析测试完成")
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
        """运行Lua解析测试"""
        try:
            result = self.test_lua_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = LuaParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 