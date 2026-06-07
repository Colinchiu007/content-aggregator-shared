# content-aggregator-shared

鍏变韩妯″潡锛?01銆?03 绛夐」鐩叡鐢級銆?
## 瀹夎

### 鏂瑰紡 1锛氭湰鍦板紑鍙?
```bash
pip install -e team/shared_modules/
```

### 鏂瑰紡 2锛氫粠 GitHub 瀹夎

```bash
pip install git+https://github.com/Colinchiu007/content-aggregator-shared.git
```

---

## 妯″潡璇存槑

### `wechat_mp/` 鈥?寰俊鍏紬鍙峰彂甯?
**鍔熻兘**锛?- 鍒涘缓鑽夌锛坄cgi-bin/draft/add`锛?- 姝ｅ紡鍙戝竷锛坄cgi-bin/freepublish/submit`锛?- 璐﹀彿绠＄悊锛堝姞瀵嗗瓨鍌級

**浣跨敤绀轰緥**锛?```python
from wechat_mp.publisher import WechatPublisher
from wechat_mp.account_store import AccountStore

store = AccountStore("data/accounts.json", master_password="your_password")
publisher = WechatPublisher(store, config)

result = publisher.publish(article)
```

**鏂囨。**锛歚docs/wechat_mp.md`

---

### `social_publish/` 鈥?鍏朵粬绀惧獟鍙戝竷锛堝緟瀹炵幇锛?
**璁″垝鏀寔**锛?- 鐧惧鍙凤紙`baidu.py`锛?- 浠婃棩澶存潯锛坄toutiao.py`锛?- 绠€涔︼紙`jianshu.py`锛?- 鐭ヤ箮锛坄zhihu.py`锛?
**褰撳墠鐘舵€?*锛氬緟 Hermes Agent 瀹炵幇銆?
---

### `auth/` 鈥?璁よ瘉妯″潡

**鍔熻兘**锛?- JWT 鐢熸垚 / 楠岃瘉锛圚S256锛?- Refresh Token锛?0 澶╋級
- FastAPI 涓棿浠讹紙`Depends(get_current_user)`锛?
**浣跨敤绀轰緥**锛?```python
from fastapi import FastAPI, Depends
from auth.auth_routes import router as auth_router
from auth.auth_middleware import get_current_user

app = FastAPI()
app.include_router(auth_router)

@app.get("/api/protected")
def protected_endpoint(user = Depends(get_current_user)):
    return {"user": user}
```

**鏂囨。**锛歚docs/auth.md`

---

## 椤圭洰缁撴瀯

```
content-aggregator-shared/
鈹溾攢鈹€ wechat_mp/                # 鍏紬鍙峰彂甯?鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹溾攢鈹€ publisher.py           # 鍙戝竷閫昏緫
鈹?  鈹斺攢鈹€ account_store.py      # 璐﹀彿鎸佷箙鍖?鈹溾攢鈹€ social_publish/            # 鍏朵粬绀惧獟鍙戝竷锛堝緟瀹炵幇锛?鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹溾攢鈹€ baidu.py             # 鐧惧鍙?鈹?  鈹溾攢鈹€ toutiao.py          # 浠婃棩澶存潯
鈹?  鈹溾攢鈹€ jianshu.py         # 绠€涔?鈹?  鈹斺攢鈹€ zhihu.py           # 鐭ヤ箮
鈹溾攢鈹€ auth/                      # 璁よ瘉妯″潡
鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹溾攢鈹€ jwt_handler.py
鈹?  鈹溾攢鈹€ auth_middleware.py
鈹?  鈹溾攢鈹€ auth_routes.py
鈹?  鈹斺攢鈹€ models.py
鈹溾攢鈹€ examples/                  # 浣跨敤绀轰緥
鈹?  鈹斺攢鈹€ usage_examples.py
鈹溾攢鈹€ docs/                      # 鏂囨。
鈹?  鈹溾攢鈹€ wechat_mp.md
鈹?  鈹斺攢鈹€ auth.md
鈹溾攢鈹€ setup.py                  # 瀹夎鑴氭湰
鈹斺攢鈹€ README.md
```

---

## 寮€鍙戣鑼?
### Git 宸ヤ綔娴?
```
main        鈫?鐢熶骇鐜锛堟墦 tag锛?develop     鈫?寮€鍙戜富骞诧紙PR 鍚堝苟鍒拌繖閲岋級
feature/xxx 鈫?鍔熻兘鍒嗘敮
```

### 鎻愪氦瑙勮寖

```
feat: 鏂板鐧惧鍙峰彂甯?fix: 淇寰俊鍙戝竷澶辫触
docs: 鏇存柊 API 鏂囨。
refactor: 閲嶆瀯鍙戝竷閫昏緫
```

### 浠ｇ爜椋庢牸

| 瑙勮寖 | 宸ュ叿 |
|------|------|
| PEP 8 | `flake8` |
| 绫诲瀷娉ㄨВ | `mypy` |
| 鏍煎紡鍖?| `black` |

---

## 浜ゆ帴淇℃伅

鏈粨搴撶敱 **QClaw (CEO)** 鍒涘缓锛岀Щ浜?**Hermes Agent** 缁х画寮€鍙戙€?
**浜ゆ帴鏂囨。**锛歚team/HANDOVER-TO-HERMES.md`

**Hermes Agent 浠诲姟**锛?1. 瀹炵幇 `social_publish/` 鍚勫钩鍙板彂甯?2. 瀹炵幇"涓€閿彂甯冨埌澶氬钩鍙?鏍稿績鍔熻兘
3. 瀹炵幇鍙戝竷鐘舵€佽窡韪紙WebSocket / 鍚庡彴浠诲姟锛?
---

## 鐗堟湰鍘嗗彶

| 鐗堟湰 | 鏃ユ湡 | 淇敼鍐呭 |
|------|------|----------|
| 0.1.0 | 2026-06-07 | 鍒濆鐗堟湰锛坄wechat_mp/` + `auth/` 浠?002/003 鎶界锛?|

---

## 璁稿彲璇?
寰呭畾锛堢敱鐢ㄦ埛鍐冲畾锛夈€?
---

*鐢?QClaw (CEO) 缁存姢锛?026-06-07 鍒涘缓銆?
