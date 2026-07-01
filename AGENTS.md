# content-aggregator-shared — 开发流程规范

> 共享模块的贡献指南与开发流程。AI 工具启动时自动读取。

---

## 核心原则

1. **共享优先**：放入本仓库的代码应被至少 2 个项目引用。单项目专用代码留在项目仓库内
2. **零循环依赖**：本模块不依赖任何下游项目（content-aggregator、Multi-Publish 等）
3. **向后兼容**：公开接口的 signature 变更需谨慎，新增功能优先加可选参数
4. **安全第一**：认证、加密模块的代码变更必须有安全审查
5. **TDD**：所有功能变更必须有测试覆盖

## AI 角色分工

| 角色 | 阶段 | 产出物 |
|------|------|--------|
| **PM** | 需求分析 | 功能说明、消费者列表 |
| **架构师** | 技术设计 | 模块设计、接口定义、兼容性方案 |
| **开发工程师** | 编码实现 | 核心逻辑 + 测试（TDD） |
| **QA** | 质量验证 | 跨项目集成测试 |
| **CTO** | 代码评审 | 安全审查、接口兼容性审查 |

## 7 阶段开发流程

### 阶段 1：需求识别
谁需要这个共享能力？
- 至少 2 个消费者确认需要
- 如果仅 1 个消费者使用 → 放在该消费者项目内

### 阶段 2：规格（PM）
产出：功能规格说明，明确：
- 接口定义（函数签名、参数、返回值）
- 消费者使用示例
- 兼容性影响（是否修改现有接口）

### 阶段 3：技术设计（架构师）
产出：模块目录结构、核心类/函数设计、边界条件
**原则：能不引入外部依赖就不引入。**

### 阶段 4：开发计划
拆成 ≤2h 的任务。

### 阶段 5：编码实现（开发 + TDD）
- 先写测试，再写实现
- 认证/加密模块变更必须有安全审查
- 在至少 1 个下游项目中验证集成

### 阶段 6：代码评审（CTO）
必检项：
- 🔴 是否有循环依赖（依赖下游项目）
- 🔴 接口 signature 是否向后兼容
- 🟠 是否引入新的外部依赖
- 🟠 测试覆盖率是否覆盖所有公开接口
- 🟢 文档是否同步更新

### 阶段 7：发布
- 更新 CHANGELOG.md（遵循 SemVer）
- git tag
- 通知消费者项目更新依赖版本


## 详细规范

本文档只包含开发流程框架。详细规范已拆分到 `references/` 子目录：

- **[references/testing.md](references/testing.md)** — TDD 流程与测试规范
- **[references/quality-gates.md](references/quality-gates.md)** — 质量门禁详细说明
- **[references/architecture.md](references/architecture.md)** — 技术约定

## 文档清单

| 文件 | 路径 | 说明 |
|------|------|------|
| AGENTS.md | `./AGENTS.md` | 本文件，开发流程规范 |
| CLAUDE.md | `./CLAUDE.md` | 项目上下文和开发命令 |
| .clinerules | `./.clinerules` | 硬约束规则 |
| PRD.md | `./docs/PRD.md` | 产品需求文档 |
| CHANGELOG.md | `./CHANGELOG.md` | 变更日志 |
| ARCHITECTURE.md | `./docs/ARCHITECTURE.md` | 架构设计文档 |
| DESIGN.md | `./docs/DESIGN.md` | 设计规范 |


## 版本号

遵循 Semantic Versioning。当前版本 **0.1.0**。

### 运行测试

```bash
cd /srv/projects/content-aggregator-shared
python -m pytest tests/ -v
```
