from datetime import datetime, timedelta
from typing import Optional, Annotated
import os

from sqlalchemy import select, update
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

import models, schemas
from db_config import DbContextManager, async_session_maker


SECRET_KEY = str(os.environ.get("SECRET_KEY"))
ALGORITHM = str(os.environ.get("ALGORITHM"))
API_PGD_ADMIN_USER = os.environ.get("API_PGD_ADMIN_USER")
API_PGD_ADMIN_PASSWORD = os.environ.get("API_PGD_ADMIN_PASSWORD")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Exceções


class InvalidCredentialsError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DisabledUserError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# ## Funções auxiliares


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, str(hashed_password))


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_all_users(
    db_session: DbContextManager,
) -> list[schemas.UsersGetSchema]:
    """Get all users from api database.

    Args:
        db_session (DbContextManager): Session with api database

    Returns:
        list[schemas.UsersGetSchema]: list of users without password
    """

    async with db_session as session:
        result = await session.execute(select(models.Users))
        users = result.scalars().all()

    return [
        schemas.UsersGetSchema(
            **schemas.UsersSchema.model_validate(user).model_dump(exclude=["password"])
        )
        for user in users
    ]


async def get_user(
    db_session: DbContextManager,
    email: str,
) -> Optional[schemas.UsersSchema]:
    async with db_session as session:
        result = await session.execute(select(models.Users).filter_by(email=email))
        user = result.unique().scalar_one_or_none()

    if user:
        return schemas.UsersSchema.model_validate(user)

    return None


async def authenticate_user(
    db: DbContextManager, username: str, password: str
) -> schemas.UsersSchema:
    """Acessa o banco de dados e verifica se o usuário existe, não está
    desabilitado e se as credenciais de acesso estão corretas. Caso tudo
    esteja certo, retorna os detalhes do usuário.

    Args:
        db (DbContextManager): Context manager contendo as informações
            necessárias para acesso ao banco de dados.
        username (str): Nome do usuário.
        password (str): Senha do usuário.

    Raises:
        InvalidCredentialsError: Caso o usuário não exista ou a senha
            esteja incorreta.
        DisabledUserError: Caso o usuário esteja desabilitado.

    Returns:
        schemas.UsersSchema: Detalhes do usuário presentes no banco de
            dados.
    """
    user = await get_user(db_session=db, email=username)

    if not user or not verify_password(password, user.password):
        raise InvalidCredentialsError("Username ou password incorretos")

    if user.disabled:
        raise DisabledUserError("Usuário desabilitado")

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def verify_token(token: str, db: DbContextManager):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais não podem ser validadas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = await get_user(db_session=db, email=token_data.username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbContextManager = Depends(DbContextManager),
):
    return await verify_token(token, db)


async def get_user_by_token(
    token: str,
    db: DbContextManager = Depends(DbContextManager),
):
    return await verify_token(token, db)


async def get_current_active_user(
    current_user: Annotated[schemas.UsersSchema, Depends(get_current_user)]
) -> Annotated[schemas.UsersSchema, Depends(get_current_user)]:
    """Check if the current user is enabled.

    Raises:
        HTTPException: User with attribute disabled = True
    """

    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuário inativo")

    return current_user


async def init_user_admin():
    db_session = async_session_maker()

    if not await get_user(db_session=db_session, email=API_PGD_ADMIN_USER):
        new_user = models.Users(
            email=API_PGD_ADMIN_USER,
            # b-crypt
            password=get_password_hash(API_PGD_ADMIN_PASSWORD),
            is_admin=True,
            origem_unidade="SIAPE",
            cod_unidade_autorizadora=1,
            sistema_gerador=f"API PGD {os.getenv('TAG_NAME', 'dev-build') or 'dev-build'}",
        )

        async with db_session as session:
            session.add(new_user)
            await session.commit()
        print(f"API_PGD_ADMIN:  Usuário administrador `{API_PGD_ADMIN_USER}` criado")
    else:
        print(f"API_PGD_ADMIN:  Usuário administrador `{API_PGD_ADMIN_USER}` já existe")


async def get_current_admin_user(
    current_user: Annotated[schemas.UsersSchema, Depends(get_current_user)]
):
    """Check if the current user is admin.

    Raises:
        HTTPException: User with attribute is_admin = False
    """

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não tem permissões de administrador",
        )

    return current_user


# ## Crud


async def create_user(
    db_session: DbContextManager,
    user: schemas.UsersSchema,
) -> schemas.UsersSchema:
    """Create user on api database.

    Args:
        db_session (DbContextManager): Session with api database
        user (schemas.UsersSchema): User to be created

    Returns:
        schemas.UsersSchema: Created user
    """

    new_user = models.Users(**user.model_dump())
    # b-crypt
    new_user.password = get_password_hash(new_user.password)
    async with db_session as session:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

    return schemas.UsersSchema.model_validate(new_user)


async def update_user(
    db_session: DbContextManager,
    user: schemas.UsersSchema,
) -> schemas.UsersSchema:
    """Update user on api database.

    Args:
        db_session (DbContextManager): Session with api database
        user (schemas.UsersSchema): User data to be updated

    Returns:
        schemas.UsersSchema: Updated user
    """

    # b-crypt
    user.password = get_password_hash(user.password)
    async with db_session as session:
        await session.execute(
            update(models.Users).filter_by(email=user.email).values(**user.model_dump())
        )
        await session.commit()

    return schemas.UsersSchema.model_validate(user)


async def user_reset_password(
    db_session: DbContextManager, token: str, new_password: str
) -> str:
    """Reset password of a user by passing a access token.

    Args:
        db_session (DbContextManager): Session with api database
        token (str): access token sended by email
        new_password (str): the new password for encryption

    Returns:
        str: Message about updated password
    """

    user = await get_user_by_token(token, db_session)

    user.password = get_password_hash(new_password)

    async with db_session as session:
        await session.execute(
            update(models.Users).filter_by(email=user.email).values(**user.model_dump())
        )
        await session.commit()

    return f"Senha do Usuário {user.email} atualizada"
