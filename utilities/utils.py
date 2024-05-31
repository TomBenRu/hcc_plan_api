import datetime
import string
import secrets

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def generate_secure_password(length: int = 12):
    if length < 12:
        raise ValueError("Password length should be at least 12 characters")

    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_characters = string.punctuation

    # Ensure the password contains at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_characters)
    ]

    # Fill the remaining length of the password with a random selection of all characters
    all_characters = lowercase + uppercase + digits + special_characters
    password += [secrets.choice(all_characters) for _ in range(length - 4)]

    # Shuffle the password list to ensure randomness
    secrets.SystemRandom().shuffle(password)

    # Convert the list to a string and return
    return ''.join(password)


def hash_psw(password: str):
    return pwd_context.hash(password)


def verify(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def all_days_between_dates(date_start: datetime.date, date_end: datetime.date):
    delta: datetime.timedelta = date_start - date_end
    all_days: list[datetime.date] = []
    for i in range(delta.days + 1):
        day = date_start + datetime.timedelta(days=i)
        all_days.append(day)
    return all_days


if __name__ == '__main__':
    print(generate_secure_password())
