from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

import config


engine = create_engine(
    'mysql+mysqldb://%s:%s@/%s?unix_socket=/cloudsql/%s' % (
        config.CLOUDSQL_USER,
        config.CLOUDSQL_PASSWORD,
        config.CLOUDSQL_DBNAME,
        config.CLOUDSQL_CONNECTION_NAME,
    )
)
db_session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()
