from sqlalchemy import create_engine, Table, Column, String, MetaData, DateTime

engine = create_engine('sqlite:///users.db')
meta = MetaData()

users = Table(
    'users', meta,
    Column('login', String(50), unique=True, nullable=False),
    Column('password', String(32), nullable=False)
)

pastes = Table(
    'pasta', meta,
    Column('user', String(50), nullable=False),
    Column('url', String(100), nullable=False),
    Column('title', String(100), unique=True, nullable=False),
    Column('paste', String(10000), nullable=False),
    Column('date', DateTime, nullable=False)
)

meta.create_all(engine)
