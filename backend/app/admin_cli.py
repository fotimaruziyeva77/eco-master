"""Admin accounts from the command line.

    python -m app.admin_cli create --login ali --name "Ali Valiyev" --role admin
    python -m app.admin_cli password --login ali
    python -m app.admin_cli reset-2fa --login ali
    python -m app.admin_cli list

The first administrator is created here; more can be added in the admin panel. Passwords
are typed at a hidden prompt, never given as arguments (those stay in the shell history).
"""

import argparse
import asyncio
import getpass

from sqlalchemy import select

from app.admin.security import hash_password, password_problem
from app.db import SessionLocal
from app.models import AdminRole, AdminUser


def ask_password() -> str:
    while True:
        password = getpass.getpass("Parol (kamida 10 belgi): ")
        if problem := password_problem(password):
            print(f"Yaroqsiz parol: {problem}")
            continue
        if getpass.getpass("Parolni takrorlang: ") != password:
            print("Parollar mos kelmadi.")
            continue
        return password


async def find(session, login: str) -> AdminUser:
    admin = await session.scalar(select(AdminUser).where(AdminUser.login == login.lower()))
    if admin is None:
        raise SystemExit(f"Admin topilmadi: {login}")
    return admin


async def create(login: str, name: str, role: str) -> None:
    async with SessionLocal() as session:
        if await session.scalar(select(AdminUser.id).where(AdminUser.login == login.lower())):
            raise SystemExit(f"Bu login band: {login}")
        session.add(
            AdminUser(
                login=login.lower(),
                name=name,
                role=AdminRole(role),
                password_hash=hash_password(ask_password()),
            )
        )
        await session.commit()
    print(f"Yaratildi: {login}. Birinchi kirishda autentifikator ilovasi ulanadi.")


async def set_password(login: str) -> None:
    async with SessionLocal() as session:
        admin = await find(session, login)
        admin.password_hash = hash_password(ask_password())
        admin.failed_logins = 0
        admin.locked_until = None
        admin.session_version += 1
        await session.commit()
    print("Parol yangilandi.")


async def reset_2fa(login: str) -> None:
    async with SessionLocal() as session:
        admin = await find(session, login)
        admin.totp_secret = None
        admin.totp_confirmed_at = None
        admin.totp_last_step = None
        admin.session_version += 1
        await session.commit()
    print("2FA o'chirildi: keyingi kirishda yangi ilova ulanadi.")


async def list_admins() -> None:
    async with SessionLocal() as session:
        for a in (await session.scalars(select(AdminUser).order_by(AdminUser.id))).all():
            state = "faol" if a.is_active else "o'chirilgan"
            twofa = "2FA bor" if a.totp_confirmed_at else "2FA yo'q"
            print(f"{a.id:>3}  {a.login:<20} {a.role.value:<7} {state:<11} {twofa}  {a.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ekoustoz admin accounts")
    commands = parser.add_subparsers(dest="command", required=True)
    create_cmd = commands.add_parser("create", help="new admin or content editor")
    create_cmd.add_argument("--login", required=True)
    create_cmd.add_argument("--name", required=True)
    # Handover point staff are created in the admin panel, where the point is chosen.
    create_cmd.add_argument("--role", choices=["admin", "editor"], default="editor")
    for name in ("password", "reset-2fa"):
        commands.add_parser(name).add_argument("--login", required=True)
    commands.add_parser("list")
    args = parser.parse_args()

    if args.command == "create":
        asyncio.run(create(args.login, args.name, args.role))
    elif args.command == "password":
        asyncio.run(set_password(args.login))
    elif args.command == "reset-2fa":
        asyncio.run(reset_2fa(args.login))
    else:
        asyncio.run(list_admins())


if __name__ == "__main__":
    main()
