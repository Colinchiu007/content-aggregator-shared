# auth package

FastAPI 认证模块（JWT + 中间件）。

## 使用方式

```python
from fastapi import FastAPI
from auth.auth_routes import router as auth_router
from auth.auth_middleware import get_current_user

app = FastAPI()
app.include_router(auth_router)

# 保护端点
@app.get("/api/protected")
def protected_endpoint(user = Depends(get_current_user)):
    return {"user": user}
```
