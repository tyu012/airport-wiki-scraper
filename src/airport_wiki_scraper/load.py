import psycopg
import os
from airport_wiki_scraper.airport import Airport
from airport_wiki_scraper.airroute import AirRouteID
from airport_wiki_scraper.utils import load_pydantic_jsonl


def load_to_db():
    CONNECTION = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD")
    }
    # print(CONNECTION)

    conn_dict = {}
    for key in CONNECTION:
        assert type(CONNECTION[key]) == str, "Database connection environment variables must be present; see README.md for more info"
        conn_dict[key] = CONNECTION[key] 

    with psycopg.connect(**conn_dict) as conn:
        print("Connected to database")

        with conn.cursor() as cur:
            create_tables(cur)

            # Delete from tables, since this is currently a full load.
            cur.execute("TRUNCATE routes")
            cur.execute("TRUNCATE airports")

            # Load to tables
            airports = load_pydantic_jsonl("data/structured/airport_info.jsonl", Airport)
            load_airports(cur, airports)

            airroutes = load_pydantic_jsonl("data/structured/airroutesid.jsonl", AirRouteID)
            load_airroutes(cur, airroutes)

    print("Done.")
            


def create_tables(cur: psycopg.Cursor):
    """
    Create tables if not exist for routes and airports.

    TODO: Verify that the primary key for routes is sufficient, detect duplicates
    """

    cur.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            origin_qid      varchar NOT NULL,
            destination_qid varchar NOT NULL,
            airline         varchar,
            seasonal        boolean,
            charter         boolean,
            begins          date,
            resumes         date,
            ends            date,
            suspended       boolean,
            PRIMARY KEY (origin_qid, destination_qid, airline, seasonal, charter)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS airports (
            qid             varchar,
            wiki_title      varchar,
            icao            varchar,
            iata            varchar,
            coordinates     point,
            PRIMARY KEY (qid)
        )
    """)


def load_airports(cur: psycopg.Cursor, airports: list[Airport]):
    """
    Load a list of Pydantic validated Airport objects to the airports table in the database.
    """
    airports_dicts = [ a.model_dump() for a in airports ]
    cur.executemany("""
        INSERT INTO airports (qid, wiki_title, icao, iata, coordinates)
        VALUES (%(qid)s, %(wiki_title)s, %(icao)s, %(iata)s, %(coordinates)s)
    """, airports_dicts)


def load_airroutes(cur: psycopg.Cursor, airroutes: list[AirRouteID]):
    """
    Load a list of Pydantic validated AirRoute objects to the airports table in the database.
    """
    routes_dicts = [ r.model_dump() for r in airroutes ]
    cur.executemany("""
        INSERT INTO routes (origin_qid, destination_qid, airline, seasonal, charter, begins, resumes, ends, suspended)
        VALUES (%(origin_qid)s, %(destination_qid)s, %(airline)s, %(seasonal)s, %(charter)s, %(begins)s, %(resumes)s, %(ends)s, %(suspended)s)
        ON CONFLICT DO NOTHING;
    """, routes_dicts)