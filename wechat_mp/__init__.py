# wechat_mp package

微信/公众号发布模块（支持多账号管理）。

## 使用方式

```python
from wechat_mp.publisher import WechatPublisher
from wechat_mp.account_store import AccountStore

# 初始化
store = AccountStore("data/accounts.json", master_password="your_password")
publisher = WechatPublisher(store, config)

# 发布文章
result = publisher.publish(article)
```
