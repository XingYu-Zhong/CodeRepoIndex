# coding: utf-8
"""
Kotlin代码解析器测试模块
测试Kotlin语言的代码解析功能
"""

import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class KotlinParserTester:
    """Kotlin解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_kotlin_test_file(self) -> Path:
        """创建Kotlin测试文件"""
        kotlin_code = '''/**
 * Kotlin测试文件
 * 包含类、数据类、扩展函数、协程等Kotlin特性
 */

package com.example.demo

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.util.*

// 枚举类
enum class UserRole(val code: String, val description: String) {
    ADMIN("admin", "管理员"),
    USER("user", "普通用户"),
    GUEST("guest", "访客");

    companion object {
        fun fromCode(code: String): UserRole? = values().find { it.code == code }
    }
}

// 数据类
data class User(
    val id: Long,
    val name: String,
    val email: String,
    val role: UserRole,
    val permissions: MutableList<String> = mutableListOf(),
    val createdAt: Date = Date()
) {
    fun hasPermission(permission: String): Boolean = permissions.contains(permission)
    
    fun addPermission(permission: String) {
        if (!hasPermission(permission)) {
            permissions.add(permission)
        }
    }
}

// 密封类
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val cause: Throwable? = null) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

// 接口
interface UserRepository {
    suspend fun findById(id: Long): User?
    suspend fun findAll(): List<User>
    suspend fun save(user: User): User
    suspend fun deleteById(id: Long): Boolean
    fun findByRoleFlow(role: UserRole): Flow<List<User>>
}

// 抽象类
abstract class BaseEntity {
    abstract val id: Long
    abstract val createdAt: Date
    
    open fun validate(): Boolean = true
    
    override fun toString(): String = "${this::class.simpleName}(id=$id)"
}

// 类继承
class UserEntity(
    override val id: Long,
    val name: String,
    val email: String,
    val role: UserRole,
    override val createdAt: Date = Date()
) : BaseEntity() {
    
    override fun validate(): Boolean {
        return name.isNotBlank() && email.contains("@") && email.contains(".")
    }
    
    override fun toString(): String = "UserEntity(id=$id, name='$name', email='$email')"
}

// 仓库实现类
class InMemoryUserRepository : UserRepository {
    private val users = mutableMapOf<Long, User>()
    private val _userFlow = MutableSharedFlow<List<User>>()
    
    override suspend fun findById(id: Long): User? = withContext(Dispatchers.IO) {
        delay(10) // 模拟IO操作
        users[id]
    }
    
    override suspend fun findAll(): List<User> = withContext(Dispatchers.IO) {
        delay(10)
        users.values.toList()
    }
    
    override suspend fun save(user: User): User = withContext(Dispatchers.IO) {
        delay(10)
        users[user.id] = user
        _userFlow.emit(users.values.toList())
        user
    }
    
    override suspend fun deleteById(id: Long): Boolean = withContext(Dispatchers.IO) {
        delay(10)
        val removed = users.remove(id) != null
        if (removed) {
            _userFlow.emit(users.values.toList())
        }
        removed
    }
    
    override fun findByRoleFlow(role: UserRole): Flow<List<User>> {
        return _userFlow.map { userList ->
            userList.filter { it.role == role }
        }
    }
}

// 服务类
class UserService(private val repository: UserRepository) {
    
    suspend fun createUser(name: String, email: String, role: UserRole): Result<User> {
        return try {
            val id = System.currentTimeMillis()
            val user = User(id, name, email, role)
            
            if (!isValidUser(user)) {
                Result.Error("用户数据无效")
            } else {
                val savedUser = repository.save(user)
                Result.Success(savedUser)
            }
        } catch (e: Exception) {
            Result.Error("创建用户失败", e)
        }
    }
    
    suspend fun getUserById(id: Long): Result<User> {
        return try {
            val user = repository.findById(id)
            if (user != null) {
                Result.Success(user)
            } else {
                Result.Error("用户不存在")
            }
        } catch (e: Exception) {
            Result.Error("获取用户失败", e)
        }
    }
    
    suspend fun getAllUsers(): Result<List<User>> {
        return try {
            val users = repository.findAll()
            Result.Success(users)
        } catch (e: Exception) {
            Result.Error("获取用户列表失败", e)
        }
    }
    
    suspend fun deleteUser(id: Long): Result<Boolean> {
        return try {
            val deleted = repository.deleteById(id)
            Result.Success(deleted)
        } catch (e: Exception) {
            Result.Error("删除用户失败", e)
        }
    }
    
    fun getUsersByRole(role: UserRole): Flow<List<User>> {
        return repository.findByRoleFlow(role)
    }
    
    private fun isValidUser(user: User): Boolean {
        return user.name.isNotBlank() && 
               user.email.contains("@") && 
               user.email.contains(".")
    }
}

// 扩展函数
fun User.isAdmin(): Boolean = role == UserRole.ADMIN

fun User.getDisplayName(): String = "$name (${role.description})"

fun List<User>.filterByPermission(permission: String): List<User> {
    return filter { it.hasPermission(permission) }
}

fun UserRole.getDefaultPermissions(): List<String> {
    return when (this) {
        UserRole.ADMIN -> listOf("READ", "WRITE", "DELETE", "ADMIN")
        UserRole.USER -> listOf("READ", "WRITE")
        UserRole.GUEST -> listOf("READ")
    }
}

// 高阶函数
fun <T> List<T>.forEachIndexedAsync(
    scope: CoroutineScope,
    action: suspend (index: Int, T) -> Unit
) {
    forEachIndexed { index, item ->
        scope.launch {
            action(index, item)
        }
    }
}

// 泛型函数
inline fun <reified T> parseJson(json: String): T? {
    return try {
        // 这里应该使用JSON解析库
        null
    } catch (e: Exception) {
        null
    }
}

// 带接收者的函数类型
fun User.apply(block: User.() -> Unit): User {
    block()
    return this
}

// 内联函数
inline fun <T> measureTime(action: () -> T): Pair<T, Long> {
    val start = System.currentTimeMillis()
    val result = action()
    val end = System.currentTimeMillis()
    return result to (end - start)
}

// 协程函数
suspend fun processUsersParallel(
    userIds: List<Long>,
    userService: UserService
): List<User> = coroutineScope {
    userIds.map { id ->
        async {
            when (val result = userService.getUserById(id)) {
                is Result.Success -> result.data
                else -> null
            }
        }
    }.awaitAll().filterNotNull()
}

// 对象声明
object UserUtils {
    const val MAX_NAME_LENGTH = 50
    const val MAX_EMAIL_LENGTH = 100
    
    fun validateEmail(email: String): Boolean {
        return email.matches(Regex("""^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"""))
    }
    
    fun generatePassword(length: Int = 12): String {
        val charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return (1..length)
            .map { charset.random() }
            .joinToString("")
    }
}

// 伴生对象
class UserFactory {
    companion object {
        fun createAdmin(name: String, email: String): User {
            return User(
                id = System.currentTimeMillis(),
                name = name,
                email = email,
                role = UserRole.ADMIN
            ).apply {
                UserRole.ADMIN.getDefaultPermissions().forEach { permission ->
                    addPermission(permission)
                }
            }
        }
        
        fun createRegularUser(name: String, email: String): User {
            return User(
                id = System.currentTimeMillis(),
                name = name,
                email = email,
                role = UserRole.USER
            ).apply {
                UserRole.USER.getDefaultPermissions().forEach { permission ->
                    addPermission(permission)
                }
            }
        }
    }
}

// 主函数
suspend fun main() {
    println("Kotlin Parser Test Program")
    println("==========================")
    
    val repository = InMemoryUserRepository()
    val userService = UserService(repository)
    
    // 创建用户
    val adminResult = userService.createUser("管理员", "admin@example.com", UserRole.ADMIN)
    val userResult = userService.createUser("普通用户", "user@example.com", UserRole.USER)
    
    when (adminResult) {
        is Result.Success -> println("创建管理员成功: ${adminResult.data}")
        is Result.Error -> println("创建管理员失败: ${adminResult.message}")
        Result.Loading -> println("正在创建管理员...")
    }
    
    when (userResult) {
        is Result.Success -> {
            println("创建用户成功: ${userResult.data}")
            
            // 测试扩展函数
            println("用户显示名称: ${userResult.data.getDisplayName()}")
            println("是否为管理员: ${userResult.data.isAdmin()}")
        }
        is Result.Error -> println("创建用户失败: ${userResult.message}")
        Result.Loading -> println("正在创建用户...")
    }
    
    // 测试协程并发
    val allUsersResult = userService.getAllUsers()
    if (allUsersResult is Result.Success) {
        val userIds = allUsersResult.data.map { it.id }
        val (users, time) = measureTime {
            runBlocking {
                processUsersParallel(userIds, userService)
            }
        }
        println("并发处理 ${users.size} 个用户，耗时 ${time}ms")
    }
    
    // 测试Flow
    val adminFlow = userService.getUsersByRole(UserRole.ADMIN)
    adminFlow.collect { adminUsers ->
        println("当前管理员用户数量: ${adminUsers.size}")
    }
}
'''
        
        temp_file = Path(tempfile.mktemp(suffix=".kt"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(kotlin_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_kotlin_parsing(self):
        """测试Kotlin解析功能"""
        logger.info("开始Kotlin解析测试")
        print("=== Kotlin解析测试 ===")
        
        test_file = self.create_kotlin_test_file()
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
        for cls in classes[:6]:
            print(f"  - {cls.name} (行 {cls.line_start}-{cls.line_end})")
        
        print(f"\n发现的函数/方法: {len(functions)}")
        for func in functions[:8]:
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{func.line_end})")
        
        logger.success("Kotlin解析测试完成")
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
        """运行Kotlin解析测试"""
        try:
            result = self.test_kotlin_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = KotlinParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 