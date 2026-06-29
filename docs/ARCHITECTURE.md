# content-aggregator-shared 架构设计

> 共享模块库的架构说明和模块组织。

---

## 定位

content-aggregator-shared 是 content-aggregator 及其下游消费者共享的工具库和认证模块。它不包含业务逻辑，只提供可复用的基础设施。

## 消费者

```
content-aggregator-shared
       |
       +---> content-aggregator (主消费者)
       |
       +---> Multi-Publish (发布端认证)
       |
       +---> platform-orchestrator (可能的集成点)
```

## 模块组织

```
content-aggregator-shared/
+-- shared/
|   +-- auth/          # JWT 认证 + OAuth2 工具
|   +-- wechat_mp/     # 微信公众号 API 封装
+-- tests/
+-- docs/
    +-- PRD.md
    +-- auth.md
    +-- wechat_mp.md
    +-- ARCHITECTURE.md
    +-- DESIGN.md
```

### auth 模块

提供 JWT 认证和 OAuth2 工具，支持 content-aggregator 和 Multi-Publish 的 SSO 集成。

核心能力：
- JWT 令牌创建和验证（HS256）
- bcrypt 密码哈希
- OAuth2 授权流程

### wechat_mp 模块

微信公众号 API 的 Python 封装，提供：
- access_token 管理（自动刷新）
- 素材上传
- 图文消息发布

## 零循环依赖约束

本模块不依赖任何下游项目。依赖链是单向的：

```
shared-models  (Tier 0 数据契约)
      |
      v
content-aggregator-shared  (共享基础设施)
      |
      v
content-aggregator / Multi-Publish  (业务模块)
      |
      v
platform-orchestrator  (整合层)
```
