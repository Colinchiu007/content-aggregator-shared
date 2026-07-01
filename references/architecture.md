# content-aggregator-shared — 技术约定

## 技术约定（项目特有）

### 修改 auth 模块

/auth 模块被 content-aggregator、Multi-Publish 等多个项目引用。修改时：

1. 不改变 JWT payload 结构（sub、username、role 字段）
2. 新增字段用可选参数，保留默认值
3. 修改密码哈希逻辑前必须通知所有下游项目
4. 在至少 1 个下游项目中验证集成

### 命名空间注意事项

当前内部导入使用 `from shared.auth.xxx import ...` 而包被安装为顶层 `auth`。修改时注意保持兼容性。

### 提交规范

```
feat(auth): 添加 OAuth2 支持
fix(wechat_mp): 修复 token 过期不刷新
docs: 更新 auth.md API 文档
chore: 升级 cryptography 到 42.0.0
```

