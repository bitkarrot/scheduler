def get_env_data_as_dict(path: str) -> dict:
    with open(path) as f:
        return dict(
            tuple(
                line.replace("\n", "").split("=")
                for line in f.readlines()
                if not line.startswith("#")
            )
        )
