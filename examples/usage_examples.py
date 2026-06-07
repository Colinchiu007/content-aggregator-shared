# 使用示例

## 示例 1：引用认证模块（001 和 003 通用）

```python
# 在 001 或 003 的 server.py 中
from fastapi import FastAPI, Depends
from auth.auth_routes import router as auth_router
from auth.auth_middleware import get_current_user

app = FastAPI()
app.include_router(auth_router)

@app.get("/api/protected")
def protected_endpoint(user = Depends(get_current_user)):
    return {"user": user}
```

---

## 示例 2：引用微信公众号发布（001 和 003 通用）

```python
from wechat_mp.publisher import WechatPublisher
from wechat_mp.account_store import AccountStore

# 初始化
store = AccountStore("data/accounts.json", master_password="your_password")
publisher = WechatPublisher(store, config)

# 发布文章
article = {
    "title": "测试文章",
    "content": "<p>这是正文</p>",
    "thumb_media_id": "xxx",
}
result = publisher.publish(article)
print(result)
```

---

## 示例 3：引用社交平台发布（003 用，001 后续也可复用）

```python
from social_publish.baidu import BaiduPublisher
from social_publish.toutiao import ToutiaoPublisher

# 初始化
baidu = BaiduPublisher(store, config)
toutiao = ToutiaoPublisher(store, config)

# 发布到百家号
result = baidu.publish(article)
print(f"百家号：{result}")

# 发布到今日头条
result = toutiao.publish(article)
print(f"今日头条：{result}")
```

---

## 示例 4：一键发布到多平台（003 核心功能）

```python
from wechat_mp.publisher import WechatPublisher
from social_publish.baidu import BaiduPublisher
from social_publish.toutiao import ToutiaoPublisher

# 初始化所有发布器
publishers = {
    "wechat": WechatPublisher(store, config),
    "baidu": BaiduPublisher(store, config),
    "toutiao": ToutiaoPublisher(store, config),
}

# 用户勾选的平台
user_selected = ["wechat", "baidu"]

# 一键发布
results = {}
for platform in user_selected:
    publisher = publishers[platform]
    results[platform] = publisher.publish(article)

print(results)
```

---

## 示例 5：本地开发时引用 shared_modules/

```bash
# 在 001 或 003 项目根目录
pip install -e ../team/shared_modules/
```

```python
# 然后正常 import
from auth.auth_routes import router
from wechat_mp.publisher import WechatPublisher
```

---

## 示例 6：生产环境通过 GitHub 安装

```bash
pip install git+https://github.com/<your-username>/content-aggregator-shared.git@main
```

```python
# 然后正常 import
from auth.auth_routes import router
from wechat_mp.publisher import WechatPublisher
```
