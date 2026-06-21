# content-aggregator-shared — 开发规范

> 共享模块的贡献指南与编码约定。

## 核心原则

1. **共享优先**：放入本仓库的代码应被至少 2 个项目引用。单项目专用代码放在项目仓库内。
2. **零循环依赖**：本模块不依赖任何下游项目（content-aggregator、Multi-Publish 等）。
3. **向后兼容**：公开接口的 signature 变更需谨慎，新增功能优先加可选参数。
4. **安全第一**：认证、加密模块的代码变更必须有安全审查。

## AI 角色分工

| 角色 | 职责 |
|------|------|
| **安全工程师** | 审查 `auth/` 和加密相关代码 |
| **开发工程师** | 实现新模块、修复 bug |
| **QA** | 跨项目集成测试 |

## 添加新模块

### 1. 创建模块目录

```
content-aggregator-shared/
└── new_module/
    ├── __init__.py      # 公开 API
    ├── core.py          # 核心逻辑
    └── models.py        # Pydantic 模型
```

### 2. 编写文档

在 `docs/` 下创建 `new_module.md`，包含：
- 功能说明
- 安装依赖
- 使用示例
- API 参考

### 3. 添加测试

```bash
mkdir tests/
touch tests/test_new_module.py
```

## 修改 auth 模块

⚠️ auth 模块被 content-aggregator、Multi-Publish 等多个项目引用。修改时：

1. **不改变 JWT payload 结构**（`sub`、`username`、`role` 字段）
2. **新增字段用可选参数**，保留默认值
3. **修改密码哈希逻辑前必须通知所有下游项目**
4. **在至少 1 个下游项目中验证集成**

## 命名空间注意事项

当前内部导入使用 `from shared.auth.xxx import ...` 而包被安装为顶层 `auth`。修改时注意保持兼容性。未来计划统一为 `shared.auth` 命名空间。

## 测试

```bash
cd /srv/projects/content-aggregator-shared
python -m pytest tests/ -v
```

## 提交规范

```
feat(auth): 添加 OAuth2 支持
fix(wechat_mp): 修复 token 过期不刷新
docs: 更新 auth.md API 文档
chore: 升级 cryptography 到 42.0.0
```

## 版本号

遵循 [Semantic Versioning](https://semver.org/)。当前版本 **0.1.0**。
