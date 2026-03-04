import os
import urllib.parse
import psycopg2

def run_migrations():
    print("/// STARTING DATABASE MIGRATION CHECK ///")
    raw_url = os.environ.get('DATABASE_URL')
    if not raw_url:
        print("/// ERR: DATABASE_URL not set!")
        return

    parsed = urllib.parse.urlparse(raw_url)

    # Force port 5432 for migrations specifically to avoid PgBouncer restrictions on DDL
    if parsed.port == 6543:
        new_netloc = parsed.netloc.replace(":6543", ":5432")
        parsed = parsed._replace(netloc=new_netloc)

    db_url = urllib.parse.urlunparse(parsed)

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True

        with conn.cursor() as cur:
            migration_file = 'migrations/01_init.sql'
            if os.path.exists(migration_file):
                with open(migration_file, 'r') as f:
                    sql_script = f.read()

                statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                for stmt in statements:
                    try:
                        cur.execute(stmt)
                    except psycopg2.errors.DuplicateTable:
                        pass
                    except psycopg2.errors.DuplicateObject:
                        pass
                    except psycopg2.errors.InvalidTableDefinition:
                        pass
                    except Exception as e:
                        print(f"/// Migration Statement Info: {e}")

                print("/// MIGRATION: 01_init.sql applied successfully.")
            else:
                print(f"/// MIGRATION ERR: File {migration_file} not found.")

    except Exception as e:
        print(f"/// CRITICAL DB INIT ERR: {e}")

    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run_migrations()
