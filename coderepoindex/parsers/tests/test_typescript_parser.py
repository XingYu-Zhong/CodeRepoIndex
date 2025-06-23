# coding: utf-8
"""
TypeScript代码解析器测试模块
测试TypeScript语言的代码解析功能
"""

import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class TypeScriptParserTester:
    """TypeScript解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_typescript_test_file(self) -> Path:
        """创建TypeScript测试文件"""
        typescript_code = '''/**
 * TypeScript测试文件
 * 包含接口、类、泛型、装饰器等TypeScript特性
 */

// 导入类型和模块
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { Component, Injectable, Input, Output, EventEmitter } from '@angular/core';

// 基础类型定义
type UserId = string;
type UserRole = 'admin' | 'user' | 'guest';

// 接口定义
interface IUser {
    id: UserId;
    name: string;
    email: string;
    role: UserRole;
    createdAt: Date;
    permissions?: string[];
}

interface IUserService {
    getUser(id: UserId): Promise<IUser>;
    updateUser(id: UserId, data: Partial<IUser>): Promise<void>;
    deleteUser(id: UserId): Promise<boolean>;
}

// 泛型接口
interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
    errors?: string[];
}

interface Repository<T, K> {
    findById(id: K): Promise<T | null>;
    findAll(): Promise<T[]>;
    create(entity: Omit<T, 'id'>): Promise<T>;
    update(id: K, data: Partial<T>): Promise<T>;
    delete(id: K): Promise<boolean>;
}

// 抽象类
abstract class BaseEntity {
    protected readonly id: string;
    protected createdAt: Date;
    protected updatedAt: Date;

    constructor(id: string) {
        this.id = id;
        this.createdAt = new Date();
        this.updatedAt = new Date();
    }

    abstract validate(): boolean;

    getId(): string {
        return this.id;
    }

    getCreatedAt(): Date {
        return this.createdAt;
    }

    protected updateTimestamp(): void {
        this.updatedAt = new Date();
    }
}

// 用户类实现
class User extends BaseEntity implements IUser {
    public name: string;
    public email: string;
    public role: UserRole;
    public permissions: string[];

    constructor(
        id: string,
        name: string,
        email: string,
        role: UserRole = 'user'
    ) {
        super(id);
        this.name = name;
        this.email = email;
        this.role = role;
        this.permissions = [];
    }

    validate(): boolean {
        return this.name.length > 0 && 
               this.email.includes('@') && 
               ['admin', 'user', 'guest'].includes(this.role);
    }

    addPermission(permission: string): void {
        if (!this.permissions.includes(permission)) {
            this.permissions.push(permission);
            this.updateTimestamp();
        }
    }

    hasPermission(permission: string): boolean {
        return this.permissions.includes(permission);
    }

    // Getter 和 Setter
    get displayName(): string {
        return `${this.name} (${this.role})`;
    }

    set userRole(role: UserRole) {
        if (['admin', 'user', 'guest'].includes(role)) {
            this.role = role;
            this.updateTimestamp();
        }
    }

    // 静态方法
    static createAdmin(name: string, email: string): User {
        const admin = new User(Date.now().toString(), name, email, 'admin');
        admin.addPermission('read');
        admin.addPermission('write');
        admin.addPermission('delete');
        return admin;
    }
}

// 装饰器
function Log(target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;
    descriptor.value = function (...args: any[]) {
        console.log(`调用方法 ${propertyName}，参数:`, args);
        const result = method.apply(this, args);
        console.log(`方法 ${propertyName} 返回:`, result);
        return result;
    };
}

function Injectable(target: any) {
    target.prototype.isInjectable = true;
    return target;
}

// 服务类
@Injectable
class UserService implements IUserService {
    private users: Map<UserId, IUser> = new Map();
    private userSubject = new BehaviorSubject<IUser[]>([]);

    @Log
    async getUser(id: UserId): Promise<IUser> {
        const user = this.users.get(id);
        if (!user) {
            throw new Error(`用户 ${id} 不存在`);
        }
        return user;
    }

    @Log
    async updateUser(id: UserId, data: Partial<IUser>): Promise<void> {
        const user = this.users.get(id);
        if (!user) {
            throw new Error(`用户 ${id} 不存在`);
        }
        
        const updatedUser = { ...user, ...data };
        this.users.set(id, updatedUser);
        this.notifyUsersChange();
    }

    @Log
    async deleteUser(id: UserId): Promise<boolean> {
        const deleted = this.users.delete(id);
        if (deleted) {
            this.notifyUsersChange();
        }
        return deleted;
    }

    private notifyUsersChange(): void {
        const allUsers = Array.from(this.users.values());
        this.userSubject.next(allUsers);
    }

    getUsersObservable(): Observable<IUser[]> {
        return this.userSubject.asObservable();
    }
}

// 泛型类
class GenericRepository<T extends BaseEntity, K = string> implements Repository<T, K> {
    private items: Map<K, T> = new Map();

    async findById(id: K): Promise<T | null> {
        return this.items.get(id) || null;
    }

    async findAll(): Promise<T[]> {
        return Array.from(this.items.values());
    }

    async create(entity: Omit<T, 'id'>): Promise<T> {
        const id = Date.now().toString() as K;
        const newEntity = { ...entity, id } as T;
        this.items.set(id, newEntity);
        return newEntity;
    }

    async update(id: K, data: Partial<T>): Promise<T> {
        const existing = this.items.get(id);
        if (!existing) {
            throw new Error('实体不存在');
        }
        
        const updated = { ...existing, ...data };
        this.items.set(id, updated);
        return updated;
    }

    async delete(id: K): Promise<boolean> {
        return this.items.delete(id);
    }
}

// Angular组件
@Component({
    selector: 'app-user-list',
    template: `
        <div class="user-list">
            <h2>用户列表</h2>
            <div *ngFor="let user of users" class="user-item">
                <span>{{user.name}} - {{user.role}}</span>
                <button (click)="onUserSelect(user)">选择</button>
            </div>
        </div>
    `
})
class UserListComponent {
    @Input() users: IUser[] = [];
    @Output() userSelected = new EventEmitter<IUser>();

    constructor(private userService: UserService) {}

    onUserSelect(user: IUser): void {
        this.userSelected.emit(user);
    }

    ngOnInit(): void {
        this.userService.getUsersObservable().subscribe(users => {
            this.users = users;
        });
    }
}

// 高级类型定义
type UserAction = 
    | { type: 'CREATE_USER'; payload: Omit<IUser, 'id'> }
    | { type: 'UPDATE_USER'; payload: { id: UserId; data: Partial<IUser> } }
    | { type: 'DELETE_USER'; payload: { id: UserId } };

// 函数类型
type UserReducer = (state: IUser[], action: UserAction) => IUser[];

// 工具函数
function createUserReducer(): UserReducer {
    return (state: IUser[], action: UserAction): IUser[] => {
        switch (action.type) {
            case 'CREATE_USER':
                const newUser: IUser = {
                    ...action.payload,
                    id: Date.now().toString()
                };
                return [...state, newUser];
            
            case 'UPDATE_USER':
                return state.map(user => 
                    user.id === action.payload.id 
                        ? { ...user, ...action.payload.data }
                        : user
                );
            
            case 'DELETE_USER':
                return state.filter(user => user.id !== action.payload.id);
            
            default:
                return state;
        }
    };
}

// 异步函数与Promise
async function fetchUserData(id: UserId): Promise<ApiResponse<IUser>> {
    try {
        const response = await fetch(`/api/users/${id}`);
        const data = await response.json();
        
        return {
            data,
            success: true,
            message: '用户数据获取成功'
        };
    } catch (error) {
        return {
            data: {} as IUser,
            success: false,
            message: '获取用户数据失败',
            errors: [error.message]
        };
    }
}

// 模块导出
export {
    IUser,
    IUserService,
    User,
    UserService,
    UserListComponent,
    GenericRepository,
    UserAction,
    UserReducer,
    createUserReducer,
    fetchUserData
};

export default UserService;
'''
        
        temp_file = Path(tempfile.mktemp(suffix=".ts"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(typescript_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_typescript_parsing(self):
        """测试TypeScript解析功能"""
        logger.info("开始TypeScript解析测试")
        print("=== TypeScript解析测试 ===")
        
        test_file = self.create_typescript_test_file()
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
        for cls in classes:
            print(f"  - {cls.name} (行 {cls.line_start}-{cls.line_end})")
        
        print(f"\n发现的函数/方法: {len(functions)}")
        for func in functions[:8]:
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{func.line_end})")
        
        logger.success("TypeScript解析测试完成")
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
        """运行TypeScript解析测试"""
        try:
            result = self.test_typescript_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = TypeScriptParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 