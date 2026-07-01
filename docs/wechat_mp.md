# 微信公众号发布模块文档

## 概述

`wechat_mp/` 提供微信公众号发布功能，支持：
- 创建草稿（`cgi-bin/draft/add`）
- 正式发布（`cgi-bin/freepublish/submit`）
- 账号管理（加密存储）

---

## 快速开始

### 安装

```bash
pip install -e ../team/shared_modules/
```

### 初始化

```python
from wechat_mp.publisher import WechatPublisher
from wechat_mp.account_store import AccountStore

# 初始化账号存储
store = AccountStore("data/accounts.json", master_password="your_password")

# 初始化发布器
publisher = WechatPublisher(store, config)
```

---

## API 参考

### `AccountStore`

**文件路径**：`wechat_mp/account_store.py`

#### 方法

| 方法 | 说明 |
|------|------|
| `__init__(filepath, master_password)` | 初始化（加密存储）|
| `add_account(platform, name, ...)` | 添加账号 |
| `get_account(platform, name)` | 获取账号（自动解密）|
| `list_accounts(platform)` | 列出所有账号 |
| `delete_account(platform, name)` | 删除账号 |

---

### `WechatPublisher`

**文件路径**：`wechat_mp/publisher.py`

#### 方法

| 方法 | 说明 |
|------|------|
| `__init__(store, config)` | 初始化（传入 AccountStore 和配置）|
| `publish(article)` | 发布文章（创建草稿或正式发布）|
| `create_draft(article)` | 创建草稿 |
| `submit_publish(media_id)` | 正式发布（需要权限）|

---

## 配置说明

### `config.yaml` 示例

```yaml
wechat:
  appid: "wx1234567890abcdef"
  secret: "your_secret"
  access_token_url: "https://api.weixin.qq.com/cgi-bin/token"
```

---

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `EnvironmentError` | 未配置 `appid` 或 `secret` | 检查 `config.yaml` |
| `requests.exceptions.HTTPError` | Access Token 无效 | 重新获取 Token |
| `PermissionError` | 公众号无发布权限 | 认证为服务号 / 企业号 |

---

## 示例

### 发布文章（创建草稿）

```python
article = {
    "title": "测试文章",
    "content": "<p>这是正文</p>",
    "thumb_media_id": "xxx",
}

result = publisher.publish(article)
print(result)
# {'success': True, 'media_id': 'xxx', 'publish_type': 'draft'}
```

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 0.1.0 | 2026-06-07 | 初始版本（从 PROJECT-003 抽离）|
