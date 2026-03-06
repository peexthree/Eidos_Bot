from sqlalchemy import Column, BigInteger, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    uid = Column(BigInteger, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    path = Column(String, default='general')
    xp = Column(BigInteger, default=0)
    biocoin = Column(BigInteger, default=0)
    level = Column(Integer, default=1)
    streak = Column(Integer, default=1)
    last_active = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    total_spent = Column(BigInteger, default=0)
    is_admin = Column(Boolean, default=False)
    # Add other columns as needed for standard usage
    is_active = Column(Boolean, default=True)

class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, ForeignKey('players.uid'))
    item_id = Column(String)
    quantity = Column(Integer, default=1)
    durability = Column(Integer, default=100)
    custom_data = Column(Text)

class RaidSession(Base):
    __tablename__ = 'raid_sessions'
    uid = Column(BigInteger, primary_key=True)
    depth = Column(BigInteger, default=0)
    signal = Column(Integer, default=100)
    buffer_xp = Column(BigInteger, default=0)
    buffer_coins = Column(BigInteger, default=0)
    mechanic_data = Column(JSON, default={})

class BotState(Base):
    __tablename__ = 'bot_states'
    uid = Column(BigInteger, primary_key=True)
    state = Column(String)
    data = Column(Text)

class Analytics(Base):
    __tablename__ = 'analytics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(BigInteger)
    event_type = Column(String)
    event_data = Column(JSON)
    timestamp = Column(TIMESTAMP, server_default=func.now())
