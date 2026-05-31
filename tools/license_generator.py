#!/usr/bin/env python3
"""厂商侧激活码生成工具。"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python-server"))

from app.license_crypto import create_license_code, format_activation_code  # noqa: E402

TOOLS_DIR = Path(__file__).resolve().parent
PRIVATE_KEY_PATH = TOOLS_DIR / "private_key.pem"


class PrivateKeyNotFoundError(FileNotFoundError):
    pass


def load_private_key() -> bytes:
    if not PRIVATE_KEY_PATH.exists():
        raise PrivateKeyNotFoundError(
            f"未找到私钥: {PRIVATE_KEY_PATH}，请先运行 python tools/generate_keypair.py"
        )
    return PRIVATE_KEY_PATH.read_bytes()


def _load_private_key() -> bytes:
    try:
        return load_private_key()
    except PrivateKeyNotFoundError as exc:
        print(str(exc))
        sys.exit(1)


def generate_activation(machine_id: str, expire: str) -> dict:
    private_key = load_private_key()
    mid = machine_id.strip().upper()
    code = create_license_code(private_key, mid, expire)
    return {
        "machine_id": mid,
        "expire": expire,
        "code": code,
    }


def generate_one(machine_id: str, expire: str) -> str:
    return generate_activation(machine_id, expire)["code"]


def generate_batch(csv_path: Path, output_path: Path) -> None:
    private_key = _load_private_key()
    rows_out = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        required = {"machine_id", "expire"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("CSV 必须包含列: machine_id, expire")

        for row in reader:
            machine_id = row["machine_id"].strip().upper()
            expire = row["expire"].strip()
            code = create_license_code(private_key, machine_id, expire)
            rows_out.append({
                "machine_id": machine_id,
                "expire": expire,
                "remark": row.get("remark", ""),
                "activation_code": code,
            })

    fieldnames = ["machine_id", "expire", "remark", "activation_code"]
    with output_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"批量生成完成: {output_path} ({len(rows_out)} 条)")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成离线激活码")
    parser.add_argument("--machine-id", help="用户机器码")
    parser.add_argument("--expire", help="到期日 YYYY-MM-DD")
    parser.add_argument("--batch", help="批量 CSV 路径 (machine_id,expire,remark)")
    parser.add_argument("--output", help="批量输出 CSV 路径", default="licenses_out.csv")
    args = parser.parse_args()

    if args.batch:
        batch_path = Path(args.batch)
        output_path = Path(args.output)
        generate_batch(batch_path, output_path)
        return 0

    if not args.machine_id or not args.expire:
        parser.error("单条生成需要 --machine-id 和 --expire")

    try:
        date.fromisoformat(args.expire)
    except ValueError:
        print("到期日格式无效，请使用 YYYY-MM-DD")
        return 1

    code = generate_one(args.machine_id, args.expire)
    print(f"激活码: {code}")
    print(f"到期日: {args.expire}")
    print(f"机器码: {args.machine_id.strip().upper()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
