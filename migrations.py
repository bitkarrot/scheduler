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
    # trunk-ignore(ruff/D401)
    """
    Initial jobs table.
    """
    await db.execute(
    """
        ALTER TABLE scheduler.jobs DROP COLUMN command TEXT;
        ALTER TABLE scheduler.jobs ADD COLUMN httpverb TEXT;
        ALTER TABLE scheduler.jobs ADD COLUMN url TEXT;
        ALTER TABLE scheduler.jobs ADD COLUMN headers JSON;
        ALTER TABLE scheduler.jobs ADD COLUMN body JSON;
    """
    )
