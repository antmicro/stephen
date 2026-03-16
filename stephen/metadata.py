from typing import List, Tuple
from datetime import datetime, timezone
from pathlib import Path
import git
import logging

import stephen.log as log

logger = logging.getLogger(__name__)


class Metadata:
    """STEPhen metadata storage class."""

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


def get_commit_info() -> Tuple[str, str]:
    """
    Retrieve Git metadata for the current working directory.

    Returns `tuple[str, str]: (sha, message)` where:
        * `sha (str)`: Full SHA hash of the current HEAD commit.
        * `message (str)`: Commit message associated with that commit.
    """
    try:
        repo = git.Repo(Path.cwd())
        sha, msg = str(repo.head.object.hexsha), str(repo.head.object.message).strip()
        logger.info("Current repo Git metadata:")
        log.progress(f"commit SHA: {sha}")
        log.progress(f"commit message: {msg}")
        return sha, msg
    except git.exc.InvalidGitRepositoryError:
        logger.warning(
            "Current workdir doesn't seem to be a Git repository, passing empty commit message and SHA strings!"
        )
        return "$", "$"
