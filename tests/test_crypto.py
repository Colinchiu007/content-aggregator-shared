"""Tests for CredentialCrypto — AES-256 encryption."""
import pytest
from content_aggregator_shared.shared.wechat_mp.crypto import CredentialCrypto, get_crypto


class TestCredentialCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        crypto = CredentialCrypto("test-master-password")
        plain = "my-secret-api-key-12345"
        encrypted = crypto.encrypt(plain)
        assert encrypted != plain
        assert crypto.decrypt(encrypted) == plain

    def test_encrypt_empty_string(self):
        crypto = CredentialCrypto("test-pwd")
        encrypted = crypto.encrypt("")
        assert crypto.decrypt(encrypted) == ""

    def test_encrypt_unicode(self):
        crypto = CredentialCrypto("test-pwd")
        plain = "中文密钥"
        encrypted = crypto.encrypt(plain)
        assert crypto.decrypt(encrypted) == plain

    def test_encrypt_long_string(self):
        crypto = CredentialCrypto("test-pwd")
        plain = "x" * 10000
        encrypted = crypto.encrypt(plain)
        assert crypto.decrypt(encrypted) == plain

    def test_decrypt_invalid_raises(self):
        crypto = CredentialCrypto("test-pwd")
        with pytest.raises(ValueError, match="解密失败"):
            crypto.decrypt("invalid-base64!!!@@@")

    def test_decrypt_tampered_ciphertext(self):
        crypto = CredentialCrypto("test-pwd")
        encrypted = crypto.encrypt("secret")
        tampered = encrypted[:-1] + ("X" if encrypted[-1] != "X" else "Y")
        with pytest.raises(ValueError, match="解密失败"):
            crypto.decrypt(tampered)

    def test_encrypt_dict(self):
        crypto = CredentialCrypto("test-pwd")
        data = {"appid": "wx123", "secret": "my-secret", "non_secret": 42}
        encrypted = crypto.encrypt_dict(data)
        assert encrypted["appid"].startswith("enc:")
        assert encrypted["secret"].startswith("enc:")
        assert encrypted["non_secret"] == 42
        assert encrypted["appid"] != data["appid"]

    def test_encrypt_dict_preserves_enc_prefix(self):
        crypto = CredentialCrypto("test-pwd")
        data = {"secret": "enc:already-encrypted-value"}
        encrypted = crypto.encrypt_dict(data)
        assert encrypted["secret"] == "enc:already-encrypted-value"

    def test_encrypt_dict_nested(self):
        crypto = CredentialCrypto("test-pwd")
        data = {"level1": {"level2": "deep-secret"}}
        encrypted = crypto.encrypt_dict(data)
        assert "enc:" in str(encrypted)

    def test_decrypt_dict_roundtrip(self):
        crypto = CredentialCrypto("test-pwd")
        original = {"appid": "wx123", "secret": "super-secret", "port": 8080}
        encrypted = crypto.encrypt_dict(original)
        decrypted = crypto.decrypt_dict(encrypted)
        assert decrypted["appid"] == "wx123"
        assert decrypted["secret"] == "super-secret"
        assert decrypted["port"] == 8080

    def test_decrypt_dict_nested(self):
        crypto = CredentialCrypto("test-pwd")
        original = {"outer": {"inner": "nested-value"}}
        encrypted = crypto.encrypt_dict(original)
        decrypted = crypto.decrypt_dict(encrypted)
        assert decrypted["outer"]["inner"] == "nested-value"

    def test_different_passwords_different_encryption(self):
        crypto1 = CredentialCrypto("pwd1")
        crypto2 = CredentialCrypto("pwd2")
        plain = "same-text"
        e1 = crypto1.encrypt(plain)
        e2 = crypto2.encrypt(plain)
        assert e1 != e2

    def test_random_key_mode(self):
        crypto = CredentialCrypto()
        plain = "test-value"
        encrypted = crypto.encrypt(plain)
        assert crypto.decrypt(encrypted) == plain


class TestGetCrypto:
    def test_singleton_behavior(self):
        c1 = get_crypto("master")
        c2 = get_crypto("master")
        assert c1 is c2

    def test_default_empty_password(self):
        c = get_crypto()
        assert c is not None
