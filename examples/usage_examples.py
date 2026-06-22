# 浣跨敤绀轰緥

## 绀轰緥 1锛氬紩鐢ㄨ璇佹ā鍧楋紙001 鍜?003 閫氱敤锛?
```python
# 鍦?001 鎴?003 鐨?server.py 涓?from fastapi import FastAPI, Depends
from auth.auth_routes import router as auth_router
from auth.auth_middleware import get_current_user

app = FastAPI()
app.include_router(auth_router)

@app.get("/api/protected")
def protected_endpoint(user = Depends(get_current_user)):
    return {"user": user}
```

---

## 绀轰緥 2锛氬紩鐢ㄥ井淇″叕浼楀彿鍙戝竷锛?01 鍜?003 閫氱敤锛?
```python
from content_aggregator_shared.shared.wechat_mp.publisher import WechatPublisher
from content_aggregator_shared.shared.wechat_mp.account_store import AccountStore

# 鍒濆鍖?store = AccountStore("data/accounts.json", master_password="your_password")
publisher = WechatPublisher(store, config)

# 鍙戝竷鏂囩珷
article = {
    "title": "娴嬭瘯鏂囩珷",
    "content": "<p>杩欐槸姝ｆ枃</p>",
    "thumb_media_id": "xxx",
}
result = publisher.publish(article)
print(result)
```

---

## 绀轰緥 3锛氬紩鐢ㄧぞ浜ゅ钩鍙板彂甯冿紙003 鐢紝001 鍚庣画涔熷彲澶嶇敤锛?
```python
from social_publish.baidu import BaiduPublisher
from social_publish.toutiao import ToutiaoPublisher

# 鍒濆鍖?baidu = BaiduPublisher(store, config)
toutiao = ToutiaoPublisher(store, config)

# 鍙戝竷鍒扮櫨瀹跺彿
result = baidu.publish(article)
print(f"鐧惧鍙凤細{result}")

# 鍙戝竷鍒颁粖鏃ュご鏉?result = toutiao.publish(article)
print(f"浠婃棩澶存潯锛歿result}")
```

---

## 绀轰緥 4锛氫竴閿彂甯冨埌澶氬钩鍙帮紙003 鏍稿績鍔熻兘锛?
```python
from content_aggregator_shared.shared.wechat_mp.publisher import WechatPublisher
from social_publish.baidu import BaiduPublisher
from social_publish.toutiao import ToutiaoPublisher

# 鍒濆鍖栨墍鏈夊彂甯冨櫒
publishers = {
    "wechat": WechatPublisher(store, config),
    "baidu": BaiduPublisher(store, config),
    "toutiao": ToutiaoPublisher(store, config),
}

# 鐢ㄦ埛鍕鹃€夌殑骞冲彴
user_selected = ["wechat", "baidu"]

# 涓€閿彂甯?results = {}
for platform in user_selected:
    publisher = publishers[platform]
    results[platform] = publisher.publish(article)

print(results)
```

---

## 绀轰緥 5锛氭湰鍦板紑鍙戞椂寮曠敤 shared_modules/

```bash
# 鍦?001 鎴?003 椤圭洰鏍圭洰褰?pip install -e ../team/shared_modules/
```

```python
# 鐒跺悗姝ｅ父 import
from auth.auth_routes import router
from content_aggregator_shared.shared.wechat_mp.publisher import WechatPublisher
```

---

## 绀轰緥 6锛氱敓浜х幆澧冮€氳繃 GitHub 瀹夎

```bash
pip install git+https://github.com/Colinchiu007/content-aggregator-shared.git@main
```

```python
# 鐒跺悗姝ｅ父 import
from auth.auth_routes import router
from content_aggregator_shared.shared.wechat_mp.publisher import WechatPublisher
```
