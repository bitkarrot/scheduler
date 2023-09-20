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
            schedule TEXT,
            httpverb TEXT,
            url TEXT,
            headers JSON,
            body JSON,
        );
    """
    )
