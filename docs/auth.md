# 认证模块文档

## 概述

`auth/` 提供 FastAPI 认证功能，支持：
- JWT 生成 / 验证（HS256）
- Refresh Token（30 天）
- 中间件（Depends(get_current_user)）

---

## 快速开始

### 安装

```bash
pip install -e ../team/shared_modules/
```

### 集成到 FastAPI

```python
from fastapi import FastAPI, Depends
from auth.auth_routes import router as auth_router
from auth.auth_middleware import get_current_user

app = FastAPI()
app.include_router(auth_router)

@app.get("/api/protected")
def protected_endpoint(user = Depends(get_current_user)):
    return {"user": user}
```

---

## API 参考

### `jwt_handler.py`

| 函数 | 说明 |
|------|------|
| `create_access_token(user_id)` | 创建 Access Token（7 天）|
| `create_refresh_token(user_id)` | 创建 Refresh Token（30 天）|
| `verify_token(token)` | 验证 Token，返回 payload |

---

### `auth_routes.py`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/refresh` | POST | 刷新 Token |
| `/api/auth/me` | GET | 获取当前用户 |

---

### `auth_middleware.py`

| 函数 | 说明 |
|------|------|
| `get_current_user(token: str = Depends(oauth2_scheme))` | 从 Authorization header 提取用户 |

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|---------|
| `JWT_SECRET` | JWT 签名密钥 | `your-secret-key`（**必须修改**）|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期 | `10080`（7 天）|
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期 | `30` |

---

## 示例

### 用户注册

```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "password": "testpass123"
}
```

**响应**：
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 0.1.0 | 2026-06-03 | 初始版本（从 PROJECT-002 抽离）|
