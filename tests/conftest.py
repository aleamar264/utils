from database.general import DefineGeneralDb
from pytest import fixture

@fixture(scope="session")
def db_params():
       yield DefineGeneralDb(
            drivername="postgresql+asyncpg",
            username="user",
            password="pass",
            host="localhost",
            database="testdb",
            port=5432,
        )