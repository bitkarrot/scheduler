async def m001_initial(db):
    # trunk-ignore(ruff/D401)
    """
    Initial jobs table.
    """
    await db.execute(
        """
        CREATE TABLE scheduler.jobs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            admin TEXT NOT NULL,
            command TEXT,
            schedule TEXT
        );
    """
    )

async def m002_add_jobs_attrs_column(db):
    """
    Initial jobs table.
    """
    await db.execute(
        """
        ALTER TABLE scheduler.jobs ADD COLUMN extra JSON
    """
    )

async def m003_update_columns_for_api(db):
    """
    Initial jobs table.
    """
    await db.execute("ALTER TABLE scheduler.jobs RENAME COLUMN command To httpverb;")
    await db.execute("ALTER TABLE scheduler.jobs ADD COLUMN status BOOLEAN NOT NULL;")
    await db.execute("ALTER TABLE scheduler.jobs ALTER COLUMN status SET DEFAULT TRUE")
    await db.execute("ALTER TABLE scheduler.jobs ADD COLUMN url TEXT;")
    await db.execute("ALTER TABLE scheduler.jobs ADD COLUMN headers JSON;")
    await db.execute("ALTER TABLE scheduler.jobs ADD COLUMN body JSON;")

async def m004_add_logging_db(db):
    """
    Add table for API call results
    """
    await db.execute(
        """
         CREATE TABLE scheduler.logs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )