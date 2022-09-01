import logging
from contextlib import suppress

from sqlalchemy import insert, select, text, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncResult

from tgbot.database.models.models import Users, Departments


async def add_user(session: AsyncSession, telegram_id, username, telegram_name):
    """  Add user to database  """
    query = insert(Users).values(telegram_id=telegram_id, username=username, telegram_name=telegram_name)
    await session.execute(query)
    with suppress(IntegrityError):
        await session.commit()


async def add_department(session: AsyncSession, title, description=None, photo_id=None):
    """  Add a new department to database  """
    query = insert(Departments).values(title=title, description=description, photo_id=photo_id)
    await session.execute(query)
    with suppress(IntegrityError):
        await session.commit()


async def get_all_departments(session: AsyncSession):
    """  Get all departments' ids and titles  """
    query = select(Departments.department_id, Departments.title)
    result = await session.execute(query)
    return result.all()


async def get_departments(session: AsyncSession, limit=None, start=1, end=None):
    """  Get departments' ids and titles by clause  """
    if end:
        subquery = select(Departments.department_id.label("d_id"), Departments.title).where(Departments.department_id <= end).limit(
            limit).order_by(Departments.department_id.desc()).subquery()
        query = select(subquery).order_by(subquery.c.d_id)
    else:
        query = select(Departments.department_id, Departments.title).where(Departments.department_id >= start).limit(limit)
    result = await session.execute(query)
    return result.all()


async def get_department(session: AsyncSession, department_id):
    """  Get a department from database by its id  """
    query = select(Departments.title, Departments.description, Departments.photo_id).where(
        Departments.department_id == department_id)
    result = await session.execute(query)
    return result.one()


async def delete_department(session: AsyncSession, department_id):
    """  Delete a department  """
    query = delete(Departments).where(Departments.department_id == department_id)
    await session.execute(query)
    await session.commit()
