# coding: utf-8
"""
Go代码解析器测试模块
测试Go语言的代码解析功能
"""

import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class GoParserTester:
    """Go解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_go_test_file(self) -> Path:
        """创建Go测试文件"""
        go_code = '''package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"gorm.io/gorm"
)

// 常量定义
const (
	ServerPort     = ":8080"
	DatabaseDriver = "postgres"
	MaxRetries     = 3
)

// 用户角色类型
type UserRole string

const (
	AdminRole UserRole = "admin"
	UserRole  UserRole = "user"
	GuestRole UserRole = "guest"
)

// 用户结构体
type User struct {
	ID          uint      `json:"id" gorm:"primaryKey"`
	Name        string    `json:"name" gorm:"not null"`
	Email       string    `json:"email" gorm:"uniqueIndex;not null"`
	Role        UserRole  `json:"role" gorm:"default:'user'"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
	Permissions []string  `json:"permissions" gorm:"-"`
}

// 用户接口
type UserRepository interface {
	GetByID(ctx context.Context, id uint) (*User, error)
	GetAll(ctx context.Context) ([]*User, error)
	Create(ctx context.Context, user *User) error
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id uint) error
}

// API响应结构体
type APIResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Message string      `json:"message,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// 数据库用户仓库实现
type dbUserRepository struct {
	db *gorm.DB
	mu sync.RWMutex
}

// 构造函数
func NewUserRepository(db *gorm.DB) UserRepository {
	return &dbUserRepository{
		db: db,
	}
}

// 根据ID获取用户
func (r *dbUserRepository) GetByID(ctx context.Context, id uint) (*User, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var user User
	err := r.db.WithContext(ctx).First(&user, id).Error
	if err != nil {
		return nil, fmt.Errorf("failed to get user by id %d: %w", id, err)
	}
	return &user, nil
}

// 获取所有用户
func (r *dbUserRepository) GetAll(ctx context.Context) ([]*User, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var users []*User
	err := r.db.WithContext(ctx).Find(&users).Error
	if err != nil {
		return nil, fmt.Errorf("failed to get all users: %w", err)
	}
	return users, nil
}

// 创建用户
func (r *dbUserRepository) Create(ctx context.Context, user *User) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if err := r.validateUser(user); err != nil {
		return fmt.Errorf("user validation failed: %w", err)
	}

	err := r.db.WithContext(ctx).Create(user).Error
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}
	return nil
}

// 更新用户
func (r *dbUserRepository) Update(ctx context.Context, user *User) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	err := r.db.WithContext(ctx).Save(user).Error
	if err != nil {
		return fmt.Errorf("failed to update user: %w", err)
	}
	return nil
}

// 删除用户
func (r *dbUserRepository) Delete(ctx context.Context, id uint) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	err := r.db.WithContext(ctx).Delete(&User{}, id).Error
	if err != nil {
		return fmt.Errorf("failed to delete user %d: %w", id, err)
	}
	return nil
}

// 验证用户数据
func (r *dbUserRepository) validateUser(user *User) error {
	if user.Name == "" {
		return fmt.Errorf("user name cannot be empty")
	}
	if user.Email == "" {
		return fmt.Errorf("user email cannot be empty")
	}
	return nil
}

// 用户服务
type UserService struct {
	repo UserRepository
}

// 构造函数
func NewUserService(repo UserRepository) *UserService {
	return &UserService{
		repo: repo,
	}
}

// 获取用户详情
func (s *UserService) GetUserDetails(ctx context.Context, id uint) (*User, error) {
	user, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return nil, err
	}

	// 加载用户权限
	user.Permissions = s.getUserPermissions(user.Role)
	return user, nil
}

// 创建新用户
func (s *UserService) CreateUser(ctx context.Context, name, email string, role UserRole) (*User, error) {
	user := &User{
		Name:      name,
		Email:     email,
		Role:      role,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := s.repo.Create(ctx, user)
	if err != nil {
		return nil, err
	}

	return user, nil
}

// 获取用户权限
func (s *UserService) getUserPermissions(role UserRole) []string {
	switch role {
	case AdminRole:
		return []string{"read", "write", "delete", "admin"}
	case UserRole:
		return []string{"read", "write"}
	case GuestRole:
		return []string{"read"}
	default:
		return []string{}
	}
}

// HTTP处理器
type UserHandler struct {
	service *UserService
}

// 构造函数
func NewUserHandler(service *UserService) *UserHandler {
	return &UserHandler{
		service: service,
	}
}

// 获取用户处理器
func (h *UserHandler) GetUser(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	idStr := vars["id"]
	
	id, err := strconv.Atoi(idStr)
	if err != nil {
		h.sendErrorResponse(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	ctx := r.Context()
	user, err := h.service.GetUserDetails(ctx, uint(id))
	if err != nil {
		h.sendErrorResponse(w, http.StatusNotFound, "User not found")
		return
	}

	h.sendSuccessResponse(w, user, "User retrieved successfully")
}

// 创建用户处理器
func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name  string   `json:"name"`
		Email string   `json:"email"`
		Role  UserRole `json:"role"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.sendErrorResponse(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	ctx := r.Context()
	user, err := h.service.CreateUser(ctx, req.Name, req.Email, req.Role)
	if err != nil {
		h.sendErrorResponse(w, http.StatusInternalServerError, "Failed to create user")
		return
	}

	h.sendSuccessResponse(w, user, "User created successfully")
}

// 发送成功响应
func (h *UserHandler) sendSuccessResponse(w http.ResponseWriter, data interface{}, message string) {
	response := APIResponse{
		Success: true,
		Data:    data,
		Message: message,
	}
	h.sendJSONResponse(w, http.StatusOK, response)
}

// 发送错误响应
func (h *UserHandler) sendErrorResponse(w http.ResponseWriter, status int, message string) {
	response := APIResponse{
		Success: false,
		Error:   message,
	}
	h.sendJSONResponse(w, status, response)
}

// 发送JSON响应
func (h *UserHandler) sendJSONResponse(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// 中间件
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
	})
}

// 认证中间件
func authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token := r.Header.Get("Authorization")
		if token == "" {
			http.Error(w, "Missing authorization token", http.StatusUnauthorized)
			return
		}

		// 这里应该验证JWT token
		// 简化示例直接检查token存在
		next.ServeHTTP(w, r)
	})
}

// 工具函数
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// 重试函数
func retry(attempts int, callback func() error) error {
	var err error
	for i := 0; i < attempts; i++ {
		if err = callback(); err == nil {
			return nil
		}
		time.Sleep(time.Duration(i) * time.Second)
	}
	return err
}

// 并发处理示例
func processUsersParallel(ctx context.Context, userIDs []uint, service *UserService) []*User {
	results := make([]*User, len(userIDs))
	var wg sync.WaitGroup
	
	for i, id := range userIDs {
		wg.Add(1)
		go func(index int, userID uint) {
			defer wg.Done()
			
			user, err := service.GetUserDetails(ctx, userID)
			if err != nil {
				log.Printf("Failed to get user %d: %v", userID, err)
				return
			}
			results[index] = user
		}(i, id)
	}
	
	wg.Wait()
	return results
}

// 主函数
func main() {
	// 这里应该初始化数据库连接
	// db := initDatabase()
	
	// 创建依赖
	// userRepo := NewUserRepository(db)
	// userService := NewUserService(userRepo)
	// userHandler := NewUserHandler(userService)

	// 创建路由
	r := mux.NewRouter()
	
	// 应用中间件
	r.Use(loggingMiddleware)
	
	// API路由
	api := r.PathPrefix("/api/v1").Subrouter()
	api.Use(authMiddleware)
	
	// 用户相关路由
	// api.HandleFunc("/users/{id}", userHandler.GetUser).Methods("GET")
	// api.HandleFunc("/users", userHandler.CreateUser).Methods("POST")

	// 启动服务器
	fmt.Printf("Server starting on port %s\n", ServerPort)
	log.Fatal(http.ListenAndServe(ServerPort, r))
}

// 初始化函数
func init() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
}
'''
        
        temp_file = Path(tempfile.mktemp(suffix=".go"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(go_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_go_parsing(self):
        """测试Go解析功能"""
        logger.info("开始Go解析测试")
        print("=== Go解析测试 ===")
        
        test_file = self.create_go_test_file()
        result = self.parser.parse_file(str(test_file))
        
        print(f"语言: {result.language.value if result.language else 'Unknown'}")
        print(f"代码片段数量: {len(result.snippets)}")
        print(f"处理时间: {result.processing_time:.4f}s")
        print(f"是否成功: {result.is_successful}")
        
        if result.errors:
            print(f"错误信息: {result.errors}")
        
        # 分析代码片段
        functions = [s for s in result.snippets if s.type in ['function', 'method']]
        
        print(f"\n发现的函数/方法: {len(functions)}")
        for func in functions[:10]:
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{func.line_end})")
        
        logger.success("Go解析测试完成")
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
        """运行Go解析测试"""
        try:
            result = self.test_go_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = GoParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 