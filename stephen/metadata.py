from typing import List
from datetime import datetime, timezone


class Metadata:
    def __init__(
        self,
        time_stamp: str | None = None,
        commit_sha: str | None = None,
        commit_msg: str | None = None,
        generator: str | None = None,
        generator_ver: str | None = None,
    ) -> None:

        self.time_stamp = datetime.now(timezone.utc).astimezone().isoformat() if not time_stamp else time_stamp
        self.commit_sha = commit_sha
        self.commit_msg = commit_msg
        self.generator = generator
        self.generator_ver = generator_ver

    @classmethod
    def get_attrs(cls) -> List[str]:
        return list(Metadata().__dict__.keys())
