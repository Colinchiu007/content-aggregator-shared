# PROJECT-000：content-aggregator-shared — PRD

> **立项日期**: 2026-06-25
> **最后更新**: 2026-06-25
> **当前版本**: v0.1.0（开发阶段）
> **产品定位**: 一站式视频生成平台的共享基础设施库，为多个子项目提供统一认证、RPA 自动化与微信发布能力
> **目标用户**: 平台各子项目（content-aggregator、platform-orchestrator 等）
> **技术架构**: Python 3.12+ / FastAPI / Playwright / JWT (HS256) / Pydantic v2

---

## 一、产品概述

### 1.1 共享库的价值

一站式视频生成平台包含 9 个子项目，其中内容采集（content-aggregator）、统一入口（platform-orchestrator）等模块存在大量重复的基础设施需求：

1. **统一认证**：所有子项目需要同一套用户注册、登录、JWT 鉴权体系，避免重复造轮子
2. **RPA 自动化**：多个项目需要浏览器自动化能力（内容采集、多平台发布），共享反检测配置与浏览器池管理
3. **微信发布**：微信公众号/图片帖（小绿书）发布逻辑可被内容聚合、多平台发布等多个项目复用
4. **消除碎片化**：避免各项目各自实现一套相似逻辑，降低维护成本与安全风险

content-aggregator-shared 定位为**纯基础设施库**，不包含任何业务逻辑，不启动独立进程，通过 `pip install -e` 方式被其他项目引用。

### 1.2 产品边界

| 包含 | 说明 |
|------|------|
| JWT 认证 | 用户注册/登录/Token 刷新/密码找回，支持 PostgreSQL 和 SQLite |
| 认证中间件 | FastAPI 依赖注入式鉴权（`Depends(get_current_user)`），含角色权限与配额检查 |
| RPA 引擎 | Playwright 浏览器启动参数、反检测配置、浏览器池管理、Cookie 持久化 |
| 微信公众平台发布 | 草稿创建/获取、图片帖（小绿书）发布、HTML 正文提取、账号凭证管理 |
| **不包含** | 业务逻辑（内容采集、改写、视频合成）、独立服务进程、前端界面、平台发布器（多平台发布逻辑在 Multi-Publish 项目中） |

---

## 二、功能模块

### 2.1 认证模块（`shared/auth/`）

提供完整的用户认证基础设施，支持 PostgreSQL 和 SQLite 双数据库后端。

#### F1-1：JWT Token 管理

| 子功能 | 描述 | 状态 |
|--------|------|------|
| Access Token 生成 | HS256 算法，含 sub/username/role/type/iat/exp 标准声明 | ✅ |
| Refresh Token 生成 | 长有效期（默认30天），仅含 sub/type 精简声明 | ✅ |
| Token 解码验证 | 自动验证签名、过期时间、必需声明 | ✅ |
| 用户信息提取 | 从 Token 解析 user_id/username/role | ✅ |
| 密钥配置 | 通过 `PO_SECRET_KEY` 或 `JWT_SECRET_KEY` 环境变量注入，支持 YAML 配置覆盖 | ✅ |

#### F1-2：用户注册/登录/鉴权

| 子功能 | 描述 | 状态 |
|--------|------|------|
| 用户注册 | 用户名+邮箱+密码，pbkdf2_sha256 哈希，自动创建 user_profiles | ✅ |
| 用户登录 | 支持用户名或邮箱登录，返回 access+refresh token | ✅ |
| Token 刷新 | 用 refresh token 换取新的 access+refresh token | ✅ |
| 获取当前用户 | `/api/auth/me` 返回完整用户资料 | ✅ |
| 密码找回 | 生成 URL 安全 token（secrets.token_urlsafe），1小时有效期 | ✅ |
| 多数据库支持 | SQLite（开发/单机） + PostgreSQL（生产）自动切换 | ✅ |

#### F1-3：FastAPI 中间件与权限控制

| 子功能 | 描述 | 状态 |
|--------|------|------|
| `get_current_user` | 强制鉴权依赖，提取 Bearer Token → 返回用户信息或 401 | ✅ |
| `get_current_user_optional` | 可选鉴权依赖，匿名用户返回 None | ✅ |
| `require_role` | 角色鉴权工厂，支持 `["admin"]` / `["admin","vip"]` 等 | ✅ |
| `check_video_quota` | 视频生成配额检查（原子操作，防并发竞态） | ✅ |
| `AuthLoggingMiddleware` | 全局中间件，记录已登录用户请求（不阻断） | ✅ |

### 2.2 RPA 引擎（`shared/rpa_engine/`）

提供浏览器自动化的基础设施，不包含具体平台发布逻辑。

#### F2：浏览器自动化基础设施

| 子功能 | 描述 | 状态 |
|--------|------|------|
| 反检测配置 | 真实 UA 列表、禁用自动化检测标志、中文时区、视口设置 | ✅ |
| 浏览器启动参数 | Playwright launch_options：channel/headless/args/viewport | ✅ |
| 人类操作模拟 | `human_delay()` 生成 300-1500ms 随机延迟 | ✅ |
| Cookie 管理（计划） | Cookie/登录态持久化 | ⏳ |
| 浏览器池管理（计划） | 浏览器实例池复用 | ⏳ |

### 2.3 微信公众平台模块（`shared/wechat_mp/`）

封装微信公众号 API 调用，支持草稿管理和图片帖发布。

#### F3：微信发布

| 子功能 | 描述 | 状态 |
|--------|------|------|
| 草稿创建 | `POST cgi-bin/draft/add`，支持 ensure_ascii=False 避免中文乱码 | ✅ |
| 草稿查询 | `POST cgi-bin/draft/get`，返回文章 HTML 内容 | ✅ |
| HTML 转纯文本 | 去除 script/style/HTML 标签，解码实体，折叠空白 | ✅ |
| 图片帖（小绿书） | `article_type=newspic`，支持 1-20 张图片，3:4 比例轮播 | ✅ |
| 标题长度控制 | 图文帖 title 上限 32 字符 | ✅ |
| 账号管理 | 账号凭证加密存储与读取 | ✅ |
| 图片生成（计划） | 自动生成配图 | ⏳ |
| 主题模板（计划） | 可配置的排版主题 | ⏳ |

---

## 三、非功能需求

### 3.1 架构约束

| 需求 | 指标 | 状态 |
|------|------|------|
| **零循环依赖** | 本库绝不依赖任何下游项目（content-aggregator、Multi-Publish 等） | ✅ |
| **最小依赖** | 仅安装必需的运行时依赖（fastapi、pyjwt、cryptography、pydantic、httpx） | ✅ |
| **Python 版本** | >= 3.12 | ✅ |
| **Pydantic v2** | 所有数据模型使用 Pydantic v2 BaseModel | ✅ |
| **双项目验证** | 新功能必须在 content-aggregator 和 platform-orchestrator 中至少验证一个 | ✅ |
| **向后兼容** | 公开接口变更需谨慎，新增功能优先加可选参数 | ✅ |

### 3.2 安全要求

| 需求 | 指标 | 状态 |
|------|------|------|
| JWT 算法 | HS256，密钥通过 `PO_SECRET_KEY` 环境变量注入（禁止硬编码） | ✅ |
| 密码哈希 | pbkdf2_sha256（passlib CryptContext） | ✅ |
| 数据库密码 | 不存储明文密码 | ✅ |
| Token 结构 | 标准 JWT 声明：sub/username/role/exp/iat/type | ✅ |
| 审计要求 | auth 模块代码变更必须经安全审查 | ✅ |
| 密钥默认值 | 仅用于开发环境；生产环境必须设置 `JWT_SECRET_KEY` | ✅ |

### 3.3 兼容性

| 需求 | 说明 | 状态 |
|------|------|------|
| PostgreSQL 兼容 | 完整支持 PostgreSQL 数据库后端 | ✅ |
| SQLite 兼容 | 开发环境/单机场景使用 SQLite（aiosqlite WAL 模式） | ✅ |
| FastAPI 集成 | 提供路由（APIRouter）和依赖注入中间件 | ✅ |
| 独立安装 | 支持 `pip install -e .` 和 `pip install git+...` | ✅ |

### 3.4 可维护性

| 需求 | 说明 | 状态 |
|------|------|------|
| 模块化 | auth/rpa_engine/wechat_mp 三模块独立，可以独立升级 | ✅ |
| 文档齐全 | 每个模块有独立文档 + 使用示例 | ✅ |
| 双归属验证 | 跨项目引用测试确保 API 稳定 | ✅ |
| 版本管理 | 遵循 Semantic Versioning，当前 v0.1.0 | ✅ |

---

## 四、使用方式

### 4.1 开发安装

```bash
# 在任一子项目中通过 editable 模式安装（开发推荐）
cd D:\Data\projects\content-aggregator-shared
pip install -e .
```

### 4.2 生产安装

```bash
pip install git+https://github.com/Colinchiu007/content-aggregator-shared.git@main
```

### 4.3 使用示例

```python
# JWT 认证
from content_aggregator_shared.shared.auth.auth_routes import router as auth_router
from content_aggregator_shared.shared.auth.auth_middleware import get_current_user

app = FastAPI()
app.include_router(auth_router)

@app.get("/api/protected")
def protected_endpoint(user=Depends(get_current_user)):
    return {"user": user}


# 微信发布
from content_aggregator_shared.shared.wechat_mp.publisher import create_draft

result = create_draft(
    access_token="xxx",
    title="测试文章",
    html="<p>正文内容</p>",
    digest="摘要",
)
print(result.media_id)


# RPA 反检测配置
from content_aggregator_shared.shared.rpa_engine.anti_detection import (
    get_browser_launch_options,
    human_delay,
)

launch_opts = get_browser_launch_options(headless=False)
```

---

## 五、当前状态

### 5.1 模块完成度

| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| `auth` 认证 | 核心功能完成 | ✅ v0.1.0 |
| `rpa_engine` RPA | 反检测配置完成，浏览器池/Cookie 管理待实现 | ⏳ 部分完成 |
| `wechat_mp` 微信 | 草稿 CRUD + 图片帖完成，图片生成/主题待实现 | ⏳ 部分完成 |

### 5.2 已知消费者

| 项目 | 引用模块 | 状态 |
|------|----------|------|
| content-aggregator | auth（注册/登录/鉴权）、wechat_mp（微信发布） | ✅ 已验证 |
| platform-orchestrator | auth（统一鉴权入口） | ✅ 已验证 |
| Multi-Publish | wechat_mp（微信发布）、rpa_engine（浏览器配置） | ⏳ 验证中 |

### 5.3 Roadmap

| 阶段 | 内容 | 状态 |
|------|------|------|
| v0.1.0 | auth 模块 + 基础 RPA 反检测 + 微信草稿发布 | ✅ 当前版本 |
| v0.2.0 | RPA 浏览器池管理、Cookie 持久化、微信图片生成 | 📅 规划中 |
| v0.3.0 | 更多共享模块提取（如内容格式化、平台适配器） | 📅 规划中 |
| v1.0.0 | 所有核心模块稳定，被 3+ 项目引用 | 📅 规划中 |

---

## 六、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| API 变更影响多个下游 | 高 | 向后兼容策略 + 可选参数 + 跨项目回归测试 |
| JWT 密钥泄露 | 高 | 仅通过环境变量注入，禁止硬编码；支持密钥轮换 |
| 模块膨胀变成"大杂烩" | 中 | 只放被 ≥2 项目引用的代码，单项目专用代码放在各自仓库 |
| 依赖冲突 | 中 | 最小化运行时依赖；激进版本范围声明 |
| WeChat API 变更 | 低 | 封装层隔离，单模块变更不影响 auth/RPA 等其他模块 |

---

## 七、验收标准

### v0.1.0 验收

- [x] **JWT 认证**：Access/Refresh Token 生成、验证、刷新完整流程
- [x] **双数据库支持**：PostgreSQL + SQLite 两种后端的用户注册/登录
- [x] **FastAPI 集成**：`auth_routes` + `auth_middleware` 可直接 `include_router`
- [x] **角色权限**：`require_role` 工厂 + `check_video_quota` 配额检查
- [x] **RPA 反检测**：浏览器启动参数、UA 伪装、人类操作延迟
- [x] **微信草稿**：创建/查询/HTML 转纯文本
- [x] **微信图片帖**：newspic 模式，支持 1-20 张图片
- [x] **零循环依赖**：不引用任何下游项目代码
- [x] **双项目验证**：已在 content-aggregator 和 platform-orchestrator 中集成auth
- [x] **文档**：AGENTS.md + 使用示例 `examples/usage_examples.py`
