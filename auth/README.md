# 共享认证模块 (shared/auth)

为 PROJECT-001、002、003 提供统一的认证能力。

## 目录结构

```
team/shared/auth/
├── __init__.py           # 模块导出
├── config.py             # 配置管理（多数据库支持）
├── jwt_handler.py        # JWT 生成/验证
├── auth_middleware.py    # FastAPI 依赖注入式鉴权
├── auth_routes.py        # 注册/登录/刷新/查询
└── models.py             # Pydantic 数据模型
```

## 快速使用

### 1. 配置

在项目 `config.yaml` 中添加：

```yaml
auth:
  jwt_secret: "your-secret-key-change-in-production"
  database_type: sqlite          # 或 postgresql
  sqlite_path: ./data/user.db    # SQLite 路径
  # database_url: "postgresql://..."  # PostgreSQL 连接（二选一）
```

### 2. 初始化数据库

**SQLite**:
```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/user.db')
conn.executescript(open('migrations/001_init_user_db.sql').read())
conn.close()
"
```

**PostgreSQL**:
```bash
psql -f migrations/001_init_user_db.sql
```

### 3. 集成到 FastAPI

```python
from fastapi import FastAPI, Depends
from shared.auth.auth_routes import router as auth_router
from shared.auth.auth_middleware import get_current_user

app = FastAPI()

# 包含认证路由（注册/登录等）
app.include_router(auth_router)

# 保护 API（需要登录）
@app.get("/api/protected")
async def protected(user=Depends(get_current_user)):
    return {"user": user}
```

### 4. 客户端登录

```bash
# 注册
curl -X POST http://localhost:8082/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123"}'

# 登录
curl -X POST http://localhost:8082/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'

# 调用受保护 API
curl http://localhost:8082/api/protected \
  -H "Authorization: Bearer <access_token>"
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/refresh` | POST | 刷新 Token |
| `/api/auth/me` | GET | 获取当前用户信息 |

## 数据库表结构

### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| uuid | TEXT | 唯一标识 |
| username | TEXT | 用户名（唯一） |
| email | TEXT | 邮箱（唯一） |
| password_hash | TEXT | 密码哈希 |
| role | TEXT | 角色（user/admin/vip） |
| is_active | BOOLEAN | 是否活跃 |
| email_verified | BOOLEAN | 邮箱是否验证 |
| last_login | TEXT | 最后登录时间 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### user_profiles 表

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INTEGER | 外键引用 users.id |
| display_name | TEXT | 显示名称 |
| avatar_url | TEXT | 头像 URL |
| subscription_plan | TEXT | 订阅计划（free/basic/pro） |
| video_quota | INTEGER | 视频配额 |
| ... | ... | 其他偏好设置 |

## 配置选项

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `JWT_SECRET_KEY` | JWT 密钥 | `dev-secret-change-in-production` |
| `DATABASE_TYPE` | 数据库类型 | `postgresql` |
| `DATABASE_URL` | PostgreSQL 连接串 | - |
| `SQLITE_PATH` | SQLite 文件路径 | `./data/user.db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期 | `10080` (7 天) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期 | `30` 天 |

## 依赖

```
fastapi
pydantic
pyjwt
passlib[bcrypt]
psycopg2-binary  # PostgreSQL
```

## 与 002 的关系

002 的 `shared/auth/` 是原始实现，已提取到 `team/shared/auth/` 作为共享模块。

002 项目目录中的 `shared/auth/` 可以删除，改为引用 `team/shared/auth/`。
