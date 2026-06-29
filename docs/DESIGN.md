# content-aggregator-shared 设计规范

> 共享模块的接口设计原则和最佳实践。

---

## 接口设计原则

### 1. 共享优先

```python
# 放入 content-aggregator-shared 的条件：
# - 被至少 2 个项目引用
# - 是跨越模块边界的能力（如认证、OAuth）

# 不放入的条件：
# - 仅 content-aggregator 内部使用
# - 强依赖特定业务上下文
```

### 2. 向后兼容

```python
# ✅ 新参数加默认值
def create_token(user_id: str, expires_in: int = 3600) -> str:
    ...

# 🔴 不能删除或重命名参数
# 🔴 不能改变参数类型
```

### 3. 纯工具，无状态

```python
# ✅ 无状态工具函数
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ❌ 有状态的类（除非跨项目需要共享状态）
class TokenManager:
    def __init__(self):  # 需要初始化的状态
        self.cache = {}
```

### 4. 安全默认值

```python
# ✅ 安全默认
def encrypt(data: bytes, key: bytes | None = None) -> bytes:
    key = key or _get_default_key()  # 明确的安全默认

# ❌ 不安全的默认
def encrypt(data: bytes, key: bytes = b"") -> bytes: ...
```

## 测试规范

```python
# tests/test_auth.py
def test_password_verify():
    hashed = hash_password("test123")
    assert verify_password("test123", hashed)
    assert not verify_password("wrong", hashed)
```

## 错误处理

```python
# 自定义异常类型
class SharedAuthError(Exception):
    """认证模块异常基类。"""

class TokenExpiredError(SharedAuthError):
    """Token 已过期。"""

class InvalidTokenError(SharedAuthError):
    """Token 无效。"""
```
