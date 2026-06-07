# content-aggregator-shared

共享模块（001、003 等项目共用）。

## 安装

### 方式 1：本地开发

```bash
pip install -e team/shared_modules/
```

### 方式 2：从 GitHub 安装

```bash
pip install git+https://github.com/<your-username>/content-aggregator-shared.git
```

---

## 模块说明

### `wechat_mp/` — 微信公众号发布

**功能**：
- 创建草稿（`cgi-bin/draft/add`）
- 正式发布（`cgi-bin/freepublish/submit`）
- 账号管理（加密存储）

**使用示例**：
```python
from wechat_mp.publisher import WechatPublisher
from wechat_mp.account_store import AccountStore

store = AccountStore("data/accounts.json", master_password="your_password")
publisher = WechatPublisher(store, config)

result = publisher.publish(article)
```

**文档**：`docs/wechat_mp.md`

---

### `social_publish/` — 其他社媒发布（待实现）

**计划支持**：
- 百家号（`baidu.py`）
- 今日头条（`toutiao.py`）
- 简书（`jianshu.py`）
- 知乎（`zhihu.py`）

**当前状态**：待 Hermes Agent 实现。

---

### `auth/` — 认证模块

**功能**：
- JWT 生成 / 验证（HS256）
- Refresh Token（30 天）
- FastAPI 中间件（`Depends(get_current_user)`）

**使用示例**：
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

**文档**：`docs/auth.md`

---

## 项目结构

```
content-aggregator-shared/
├── wechat_mp/                # 公众号发布
│   ├── __init__.py
│   ├── publisher.py           # 发布逻辑
│   └── account_store.py      # 账号持久化
├── social_publish/            # 其他社媒发布（待实现）
│   ├── __init__.py
│   ├── baidu.py             # 百家号
│   ├── toutiao.py          # 今日头条
│   ├── jianshu.py         # 简书
│   └── zhihu.py           # 知乎
├── auth/                      # 认证模块
│   ├── __init__.py
│   ├── jwt_handler.py
│   ├── auth_middleware.py
│   ├── auth_routes.py
│   └── models.py
├── examples/                  # 使用示例
│   └── usage_examples.py
├── docs/                      # 文档
│   ├── wechat_mp.md
│   └── auth.md
├── setup.py                  # 安装脚本
└── README.md
```

---

## 开发规范

### Git 工作流

```
main        ← 生产环境（打 tag）
develop     ← 开发主干（PR 合并到这里）
feature/xxx ← 功能分支
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
| PEP 8 | `flake8` |
| 类型注解 | `mypy` |
| 格式化 | `black` |

---

## 交接信息

本仓库由 **QClaw (CEO)** 创建，移交 **Hermes Agent** 继续开发。

**交接文档**：`team/HANDOVER-TO-HERMES.md`

**Hermes Agent 任务**：
1. 实现 `social_publish/` 各平台发布
2. 实现"一键发布到多平台"核心功能
3. 实现发布状态跟踪（WebSocket / 后台任务）

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 0.1.0 | 2026-06-07 | 初始版本（`wechat_mp/` + `auth/` 从 002/003 抽离） |

---

## 许可证

待定（由用户决定）。

---

*由 QClaw (CEO) 维护，2026-06-07 创建。*
