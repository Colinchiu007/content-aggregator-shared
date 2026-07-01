# content-aggregator-shared

> 共享模块：JWT 鉴权 + RPA 引擎 + 微信发布。供 content-aggregator、Multi-Publish 等项目共用。

## 模块说明

### auth/ — JWT 鉴权模块
- JWT 生成 / 验证（HS256）
- Refresh Token（30 天）
- FastAPI 中间件（Depends(get_current_user)）
- 用户注册 / 登录 / 密码重置端点

详见 [docs/auth.md](docs/auth.md)

### wechat_mp/ — 微信公众号发布
- 创建草稿（cgi-bin/draft/add）
- 正式发布（cgi-bin/freepublish/submit）
- 账号管理（加密存储）

详见 [docs/wechat_mp.md](docs/wechat_mp.md)

### social_publish/ — 其他社媒发布（待实现）
计划支持：百家号、今日头条、简书、知乎

## 安装

### 方式 1：本地开发
```bash
pip install -e .
```

### 方式 2：从 GitHub 安装
```bash
pip install git+https://github.com/Colinchiu007/content-aggregator-shared.git
```

## 快速示例

### JWT 鉴权
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

### 微信发布
```python
from wechat_mp.publisher import WechatPublisher
from wechat_mp.account_store import AccountStore

store = AccountStore("data/accounts.json", master_password="your_password")
publisher = WechatPublisher(store, config)
result = publisher.publish(article)
```

## 依赖
- fastapi >= 0.100.0
- pyjwt >= 2.8.0
- httpx >= 0.27.0
- cryptography >= 42.0.0
- pydantic >= 2.0.0

## 项目结构
```
content-aggregator-shared/
├── auth/                      # JWT鉴权模块
├── wechat_mp/                 # 微信公众号发布
├── social_publish/            # 其他社媒发布（待实现）
├── examples/                  # 使用示例
├── docs/                      # 文档
├── setup.py
└── README.md
```

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 0.1.0 | 2026-06-07 | 初始版本（wechat_mp/ + auth/ 从 002/003 抽取） |

## 开发规范

### Git 工作流
```
main        → 生产环境（打 tag）
develop     → 开发主干（PR 合并到这里）
feature/xxx → 功能分支
```

### 提交规范
```
feat: 新增百家号发布
fix: 修复微信发布失败
docs: 更新 API 文档
refactor: 重构发布逻辑
```

### 代码风格
| 规范 | 工具 |
|------|------|
| PEP 8 | flake8 |
| 类型注解 | mypy |
| 格式化 | black |

## License
待定（由用户决定）。
