# coding: utf-8
"""
C代码解析器测试模块
测试C语言的代码解析功能
"""

import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class CParserTester:
    """C解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_c_test_file(self) -> Path:
        """创建C测试文件"""
        c_code = '''/*
 * C语言测试文件
 * 包含结构体、函数、指针等C语言特性
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <pthread.h>

// 宏定义
#define MAX_USERS 1000
#define USERNAME_LENGTH 50
#define EMAIL_LENGTH 100
#define SUCCESS 0
#define ERROR -1

// 枚举类型
typedef enum {
    USER_ROLE_ADMIN,
    USER_ROLE_USER,
    USER_ROLE_GUEST
} UserRole;

// 用户结构体
typedef struct {
    int id;
    char name[USERNAME_LENGTH];
    char email[EMAIL_LENGTH];
    UserRole role;
    bool is_active;
    time_t created_at;
} User;

// 用户管理器结构体
typedef struct {
    User users[MAX_USERS];
    int count;
    pthread_mutex_t mutex;
} UserManager;

// 函数指针类型
typedef int (*UserValidator)(const User* user);
typedef void (*UserProcessor)(User* user);

// 全局变量
static UserManager g_user_manager = {0};
static bool g_initialized = false;

// 函数声明
int init_user_manager(void);
void cleanup_user_manager(void);
int create_user(const char* name, const char* email, UserRole role);
User* find_user_by_id(int id);
int update_user(int id, const User* user_data);
int delete_user(int id);
void print_user(const User* user);
bool validate_user(const User* user);
const char* role_to_string(UserRole role);

// 初始化用户管理器
int init_user_manager(void) {
    if (g_initialized) {
        return SUCCESS;
    }

    memset(&g_user_manager, 0, sizeof(UserManager));
    
    if (pthread_mutex_init(&g_user_manager.mutex, NULL) != 0) {
        fprintf(stderr, "Failed to initialize mutex\\n");
        return ERROR;
    }

    g_initialized = true;
    printf("User manager initialized successfully\\n");
    return SUCCESS;
}

// 清理用户管理器
void cleanup_user_manager(void) {
    if (!g_initialized) {
        return;
    }

    pthread_mutex_destroy(&g_user_manager.mutex);
    g_initialized = false;
    printf("User manager cleaned up\\n");
}

// 创建用户
int create_user(const char* name, const char* email, UserRole role) {
    if (!g_initialized) {
        fprintf(stderr, "User manager not initialized\\n");
        return ERROR;
    }

    if (name == NULL || email == NULL) {
        fprintf(stderr, "Invalid parameters\\n");
        return ERROR;
    }

    pthread_mutex_lock(&g_user_manager.mutex);

    if (g_user_manager.count >= MAX_USERS) {
        pthread_mutex_unlock(&g_user_manager.mutex);
        fprintf(stderr, "Maximum users reached\\n");
        return ERROR;
    }

    User* new_user = &g_user_manager.users[g_user_manager.count];
    new_user->id = g_user_manager.count + 1;
    strncpy(new_user->name, name, USERNAME_LENGTH - 1);
    new_user->name[USERNAME_LENGTH - 1] = '\\0';
    strncpy(new_user->email, email, EMAIL_LENGTH - 1);
    new_user->email[EMAIL_LENGTH - 1] = '\\0';
    new_user->role = role;
    new_user->is_active = true;
    new_user->created_at = time(NULL);

    if (!validate_user(new_user)) {
        pthread_mutex_unlock(&g_user_manager.mutex);
        fprintf(stderr, "User validation failed\\n");
        return ERROR;
    }

    g_user_manager.count++;
    pthread_mutex_unlock(&g_user_manager.mutex);

    printf("User created: ID=%d, Name=%s\\n", new_user->id, new_user->name);
    return new_user->id;
}

// 根据ID查找用户
User* find_user_by_id(int id) {
    if (!g_initialized || id <= 0) {
        return NULL;
    }

    pthread_mutex_lock(&g_user_manager.mutex);

    for (int i = 0; i < g_user_manager.count; i++) {
        if (g_user_manager.users[i].id == id) {
            pthread_mutex_unlock(&g_user_manager.mutex);
            return &g_user_manager.users[i];
        }
    }

    pthread_mutex_unlock(&g_user_manager.mutex);
    return NULL;
}

// 更新用户
int update_user(int id, const User* user_data) {
    if (!g_initialized || user_data == NULL) {
        return ERROR;
    }

    User* user = find_user_by_id(id);
    if (user == NULL) {
        fprintf(stderr, "User not found: ID=%d\\n", id);
        return ERROR;
    }

    pthread_mutex_lock(&g_user_manager.mutex);

    strncpy(user->name, user_data->name, USERNAME_LENGTH - 1);
    user->name[USERNAME_LENGTH - 1] = '\\0';
    strncpy(user->email, user_data->email, EMAIL_LENGTH - 1);
    user->email[EMAIL_LENGTH - 1] = '\\0';
    user->role = user_data->role;
    user->is_active = user_data->is_active;

    pthread_mutex_unlock(&g_user_manager.mutex);

    printf("User updated: ID=%d\\n", id);
    return SUCCESS;
}

// 删除用户
int delete_user(int id) {
    if (!g_initialized) {
        return ERROR;
    }

    pthread_mutex_lock(&g_user_manager.mutex);

    for (int i = 0; i < g_user_manager.count; i++) {
        if (g_user_manager.users[i].id == id) {
            // 移动后续元素
            for (int j = i; j < g_user_manager.count - 1; j++) {
                g_user_manager.users[j] = g_user_manager.users[j + 1];
            }
            g_user_manager.count--;
            pthread_mutex_unlock(&g_user_manager.mutex);
            printf("User deleted: ID=%d\\n", id);
            return SUCCESS;
        }
    }

    pthread_mutex_unlock(&g_user_manager.mutex);
    fprintf(stderr, "User not found: ID=%d\\n", id);
    return ERROR;
}

// 打印用户信息
void print_user(const User* user) {
    if (user == NULL) {
        printf("User: NULL\\n");
        return;
    }

    printf("User ID: %d\\n", user->id);
    printf("Name: %s\\n", user->name);
    printf("Email: %s\\n", user->email);
    printf("Role: %s\\n", role_to_string(user->role));
    printf("Active: %s\\n", user->is_active ? "Yes" : "No");
    printf("Created: %s", ctime(&user->created_at));
}

// 验证用户数据
bool validate_user(const User* user) {
    if (user == NULL) {
        return false;
    }

    if (strlen(user->name) == 0) {
        return false;
    }

    if (strlen(user->email) == 0 || strstr(user->email, "@") == NULL) {
        return false;
    }

    return true;
}

// 角色转字符串
const char* role_to_string(UserRole role) {
    switch (role) {
        case USER_ROLE_ADMIN:
            return "Admin";
        case USER_ROLE_USER:
            return "User";
        case USER_ROLE_GUEST:
            return "Guest";
        default:
            return "Unknown";
    }
}

// 批量处理用户
void process_users_batch(UserProcessor processor) {
    if (!g_initialized || processor == NULL) {
        return;
    }

    pthread_mutex_lock(&g_user_manager.mutex);

    for (int i = 0; i < g_user_manager.count; i++) {
        processor(&g_user_manager.users[i]);
    }

    pthread_mutex_unlock(&g_user_manager.mutex);
}

// 用户处理器示例
void activate_user_processor(User* user) {
    if (user != NULL) {
        user->is_active = true;
    }
}

void deactivate_user_processor(User* user) {
    if (user != NULL) {
        user->is_active = false;
    }
}

// 内存分配相关函数
User* allocate_user(void) {
    User* user = (User*)malloc(sizeof(User));
    if (user != NULL) {
        memset(user, 0, sizeof(User));
    }
    return user;
}

void free_user(User* user) {
    if (user != NULL) {
        free(user);
    }
}

// 字符串工具函数
char* copy_string(const char* src) {
    if (src == NULL) {
        return NULL;
    }

    size_t len = strlen(src) + 1;
    char* dest = (char*)malloc(len);
    if (dest != NULL) {
        strcpy(dest, src);
    }
    return dest;
}

// 主函数
int main(int argc, char* argv[]) {
    printf("C Parser Test Program\\n");
    printf("=====================\\n");

    if (init_user_manager() != SUCCESS) {
        fprintf(stderr, "Failed to initialize user manager\\n");
        return EXIT_FAILURE;
    }

    // 创建测试用户
    int user1_id = create_user("张三", "zhangsan@example.com", USER_ROLE_ADMIN);
    int user2_id = create_user("李四", "lisi@example.com", USER_ROLE_USER);
    int user3_id = create_user("王五", "wangwu@example.com", USER_ROLE_GUEST);

    // 查找并打印用户
    User* user = find_user_by_id(user1_id);
    if (user != NULL) {
        printf("\\nFound user:\\n");
        print_user(user);
    }

    // 批量激活用户
    printf("\\nActivating all users...\\n");
    process_users_batch(activate_user_processor);

    // 清理
    cleanup_user_manager();
    return EXIT_SUCCESS;
}
'''
        
        temp_file = Path(tempfile.mktemp(suffix=".c"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(c_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_c_parsing(self):
        """测试C解析功能"""
        logger.info("开始C解析测试")
        print("=== C解析测试 ===")
        
        test_file = self.create_c_test_file()
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
        
        logger.success("C解析测试完成")
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
        """运行C解析测试"""
        try:
            result = self.test_c_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = CParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 