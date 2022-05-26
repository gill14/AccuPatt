from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine

# engine = create_engine('sqlite:///sales.db', echo = True)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Series(Base):
    __tablename__ = "series"
    id = Column(Integer, primary_key=True)

    series = Column(Integer)
    created = Column(Integer)
    modified = Column(Integer)
    notes_setup = Column(String)
    notes_analyst = Column(String)
    version_major = Column(Integer)
    version_minor = Column(Integer)
    version_release = Column(Integer)


# Base.metadata.create_all(engine)
