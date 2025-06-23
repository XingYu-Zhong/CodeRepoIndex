# coding: utf-8
"""
Java代码解析器测试模块
测试Java语言的代码解析功能
"""

import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class JavaParserTester:
    """Java解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_java_test_file(self) -> Path:
        """创建Java测试文件"""
        java_code = '''package com.example.demo;

import java.util.*;
import java.util.concurrent.*;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.*;

/**
 * Java测试文件
 * 包含类、接口、注解、泛型等Java特性
 */

// 用户角色枚举
public enum UserRole {
    ADMIN("admin", "管理员"),
    USER("user", "普通用户"),
    GUEST("guest", "访客");

    private final String code;
    private final String description;

    UserRole(String code, String description) {
        this.code = code;
        this.description = description;
    }

    public String getCode() { return code; }
    public String getDescription() { return description; }
}

// 用户接口
public interface UserRepository {
    Optional<User> findById(Long id);
    List<User> findAll();
    User save(User user);
    void deleteById(Long id);
    List<User> findByRole(UserRole role);
}

// 抽象基类
public abstract class BaseEntity {
    protected Long id;
    protected Date createdAt;
    protected Date updatedAt;

    public BaseEntity() {
        this.createdAt = new Date();
        this.updatedAt = new Date();
    }

    // 抽象方法
    public abstract boolean validate();

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public Date getCreatedAt() { return createdAt; }
    public Date getUpdatedAt() { return updatedAt; }
    
    protected void updateTimestamp() {
        this.updatedAt = new Date();
    }
}

// 用户实体类
public class User extends BaseEntity {
    private String name;
    private String email;
    private UserRole role;
    private List<String> permissions;

    // 构造函数
    public User() {
        super();
        this.permissions = new ArrayList<>();
    }

    public User(String name, String email, UserRole role) {
        this();
        this.name = name;
        this.email = email;
        this.role = role;
    }

    @Override
    public boolean validate() {
        return name != null && !name.trim().isEmpty() 
               && email != null && email.contains("@")
               && role != null;
    }

    // 业务方法
    public void addPermission(String permission) {
        if (!permissions.contains(permission)) {
            permissions.add(permission);
            updateTimestamp();
        }
    }

    public boolean hasPermission(String permission) {
        return permissions.contains(permission);
    }

    // 静态工厂方法
    public static User createAdmin(String name, String email) {
        User admin = new User(name, email, UserRole.ADMIN);
        admin.addPermission("READ");
        admin.addPermission("WRITE");
        admin.addPermission("DELETE");
        return admin;
    }

    // Getters and Setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public UserRole getRole() { return role; }
    public void setRole(UserRole role) { this.role = role; }
    
    public List<String> getPermissions() { return new ArrayList<>(permissions); }
}

// 泛型仓库类
public class GenericRepository<T extends BaseEntity, ID> {
    private final Map<ID, T> storage = new ConcurrentHashMap<>();

    public Optional<T> findById(ID id) {
        return Optional.ofNullable(storage.get(id));
    }

    public List<T> findAll() {
        return new ArrayList<>(storage.values());
    }

    public T save(T entity) {
        @SuppressWarnings("unchecked")
        ID id = (ID) entity.getId();
        storage.put(id, entity);
        return entity;
    }

    public boolean delete(ID id) {
        return storage.remove(id) != null;
    }

    public long count() {
        return storage.size();
    }
}

// 服务类
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;

    private final ExecutorService executorService = 
        Executors.newFixedThreadPool(10);

    /**
     * 获取用户详情
     */
    public Optional<User> getUserById(Long id) {
        return userRepository.findById(id);
    }

    /**
     * 创建新用户
     */
    public User createUser(String name, String email, UserRole role) {
        User user = new User(name, email, role);
        if (!user.validate()) {
            throw new IllegalArgumentException("用户数据无效");
        }
        return userRepository.save(user);
    }

    /**
     * 批量处理用户
     */
    public CompletableFuture<List<User>> processUsersAsync(List<Long> userIds) {
        return CompletableFuture.supplyAsync(() -> {
            return userIds.stream()
                .map(this::getUserById)
                .filter(Optional::isPresent)
                .map(Optional::get)
                .collect(Collectors.toList());
        }, executorService);
    }

    /**
     * 根据角色过滤用户
     */
    public List<User> getUsersByRole(UserRole role) {
        return userRepository.findByRole(role);
    }
}

// REST控制器
@RestController
@RequestMapping("/api/v1/users")
public class UserController {
    @Autowired
    private UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        Optional<User> user = userService.getUserById(id);
        return user.map(u -> ResponseEntity.ok(u))
                  .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody CreateUserRequest request) {
        try {
            User user = userService.createUser(
                request.getName(), 
                request.getEmail(), 
                request.getRole()
            );
            return ResponseEntity.ok(user);
        } catch (Exception e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @GetMapping
    public ResponseEntity<List<User>> getUsersByRole(
            @RequestParam(required = false) UserRole role) {
        List<User> users = role != null 
            ? userService.getUsersByRole(role)
            : userService.getAllUsers();
        return ResponseEntity.ok(users);
    }
}

// 请求DTO
public class CreateUserRequest {
    private String name;
    private String email;
    private UserRole role;

    // 默认构造函数
    public CreateUserRequest() {}

    // 全参构造函数
    public CreateUserRequest(String name, String email, UserRole role) {
        this.name = name;
        this.email = email;
        this.role = role;
    }

    // Getters and Setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public UserRole getRole() { return role; }
    public void setRole(UserRole role) { this.role = role; }
}

// 工具类
public final class UserUtils {
    private UserUtils() {
        throw new UnsupportedOperationException("工具类不能实例化");
    }

    public static boolean isValidEmail(String email) {
        return email != null && email.contains("@") && email.contains(".");
    }

    public static String generateDisplayName(User user) {
        return String.format("%s (%s)", user.getName(), user.getRole().getDescription());
    }

    public static List<User> filterByPermission(List<User> users, String permission) {
        return users.stream()
                   .filter(user -> user.hasPermission(permission))
                   .collect(Collectors.toList());
    }
}
'''
        
        temp_file = Path(tempfile.mktemp(suffix=".java"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(java_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_java_parsing(self):
        """测试Java解析功能"""
        logger.info("开始Java解析测试")
        print("=== Java解析测试 ===")
        
        test_file = self.create_java_test_file()
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
        
        print(f"\n发现的方法: {len(functions)}")
        for func in functions[:8]:
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{func.line_end})")
        
        logger.success("Java解析测试完成")
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
        """运行Java解析测试"""
        try:
            result = self.test_java_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = JavaParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 