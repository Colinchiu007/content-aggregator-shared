# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-06-27

### Added
- 测试基础设施：89 个测试用例覆盖 6 个模块
  - `tests/test_models.py`：PlatformType、TaskStatus、PublishTask、PublishResult、PlatformAccount
  - `tests/test_crypto.py`：CredentialCrypto 加解密、encrypt_dict/decrypt_dict、singleton
  - `tests/test_publisher.py`：DraftResult、ImagePostResult、html_to_plaintext
  - `tests/test_jwt_handler.py`：create_access_token、create_refresh_token、decode_token、get_user_from_token
  - `tests/test_anti_detection.py`：get_browser_launch_options、human_delay、REAL_USER_AGENTS
  - `tests/test_wechat_api.py`：DraftResult str、ImagePostResult counts、html_to_plaintext

## [0.1.1] - 2026-06-26

### Changed
- JWT 默认密钥移除（环境变量强制）
- FastAPI 依赖注入中间件完善
- RPA 反检测配置

## [0.1.0] - 2026-06-25

### Added
- 初始版本，JWT 认证模块（python-jose HS256）
- Playwright RPA 引擎框架
- 微信发布模块基础
