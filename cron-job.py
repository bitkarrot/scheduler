# imports go here

# extract job_id param
# query DB for job

async with httpx.AsyncClient() as client:
    resp = await client.get(    # action can be any HTTP verb (GET, PUT, POST, etc) set in the job config
        url,                    # from the job config
        headers,                # from the job config
    )
    save_job_execution(resp.status_code, resp.text())
