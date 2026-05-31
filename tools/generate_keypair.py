#!/usr/bin/env python3
"""一次性生成 Ed25519 密钥对，并更新客户端公钥。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
PRIVATE_KEY_PATH = TOOLS_DIR / "private_key.pem"
PUBLIC_KEY_PATH = TOOLS_DIR / "public_key.pem"
LICENSE_CRYPTO_PATH = ROOT / "python-server" / "app" / "license_crypto.py"


def main() -> int:
    if PRIVATE_KEY_PATH.exists():
        print(f"私钥已存在: {PRIVATE_KEY_PATH}")
        print("如需重新生成，请先手动删除 private_key.pem 和 public_key.pem")
        return 1

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    PRIVATE_KEY_PATH.write_bytes(private_pem)
    PUBLIC_KEY_PATH.write_bytes(public_pem)

    content = LICENSE_CRYPTO_PATH.read_text(encoding="utf-8")
    pattern = r'PUBLIC_KEY_PEM = b"""[\s\S]*?"""'
    pem_text = public_pem.decode("utf-8").strip()
    replacement = f'PUBLIC_KEY_PEM = b"""{pem_text}\n"""'
    updated, count = re.subn(pattern, replacement, content, count=1)
    if count != 1:
        print("未能更新 license_crypto.py 中的 PUBLIC_KEY_PEM")
        return 1

    LICENSE_CRYPTO_PATH.write_text(updated, encoding="utf-8")

    print("密钥对生成成功:")
    print(f"  私钥: {PRIVATE_KEY_PATH}")
    print(f"  公钥: {PUBLIC_KEY_PATH}")
    print(f"  已写入公钥到: {LICENSE_CRYPTO_PATH}")
    print("\n请妥善保管 private_key.pem，不要提交到 git 或随客户端分发。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
