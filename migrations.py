async def m001_initial(db):
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
