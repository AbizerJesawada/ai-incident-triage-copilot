from getpass import getpass

from sqlalchemy import select

from app.auth_service import hash_password
from app.database import SessionLocal
from app.models import User


def main() -> None:
    email = input("Engineer email: ").strip().lower()
    full_name = input("Engineer full name: ").strip()
    password = getpass("Engineer password: ")

    if not email or "@" not in email:
        raise SystemExit("Enter a valid email address.")

    if len(full_name) < 2:
        raise SystemExit("Engineer name must have at least 2 characters.")

    if len(password) < 8:
        raise SystemExit("Password must have at least 8 characters.")

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user is not None:
            raise SystemExit("An account already exists with this email.")

        engineer = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role="engineer",
        )

        db.add(engineer)
        db.commit()

    print(f"Engineer account created for {email}.")


if __name__ == "__main__":
    main()