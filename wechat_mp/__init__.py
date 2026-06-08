"""
微信公众号发布模块（合并版）

来源：
- wechat_publisher/ (PROJECT-001): 文章排版转换、主题系统、AI配图、CLI
- multi_publish (PROJECT-003): AccountStore 账号持久化、凭证加密、数据模型

提供：
- 文章转换（Markdown → 微信公众号 HTML + 主题）
- AI 配图生成（8 个供应商）
- 账号持久化（加密存储 + CRUD）
- CLI 工具
"""

# 来自 PROJECT-001 (wechat_publisher)
from wechat_mp.publisher import create_draft, get_draft, html_to_plaintext, create_image_post, DraftResult, ImagePostResult
from wechat_mp.wechat_api import get_access_token, ensure_valid_token, upload_image, upload_thumb, TokenResult
from wechat_mp.converter import WeChatConverter, ConvertResult, preview_html
from wechat_mp.theme import Theme, load_theme, list_themes, get_inline_css_rules
from wechat_mp.image_gen import generate_image, ImageProvider
from wechat_mp.config import load_config, get_config_path, get_wechat_credentials

# 来自 PROJECT-003 (multi_publish)
from wechat_mp.models import PlatformAccount, PlatformType, PublishResult
from wechat_mp.crypto import CredentialCrypto
from wechat_mp.account_store import AccountStore

__all__ = [
    # Publisher
    "create_draft", "get_draft", "html_to_plaintext", "create_image_post",
    "DraftResult", "ImagePostResult",
    # WeChat API
    "get_access_token", "ensure_valid_token", "upload_image", "upload_thumb",
    "TokenResult",
    # Converter
    "WeChatConverter", "ConvertResult", "preview_html",
    # Theme
    "Theme", "load_theme", "list_themes", "get_inline_css_rules",
    # Image Gen
    "generate_image", "ImageProvider",
    # Config
    "load_config", "get_config_path", "get_wechat_credentials",
    # Platform Models
    "PlatformAccount", "PlatformType", "PublishResult",
    # Crypto
    "CredentialCrypto",
    # Account Store
    "AccountStore",
]
