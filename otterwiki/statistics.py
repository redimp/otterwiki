from datetime import datetime, timedelta
from typing import List, Tuple

from otterwiki.gitstorage import GitStorage


class StatisticsService:
    def __init__(self, repository_path: str):
        self.storage = GitStorage(repository_path)

    def _aggregate_commits(
        self,
        log_entries: List[dict],
        since_days: int | None = None,
    ) -> List[Tuple[str, int]]:

        stats = {}
        now = datetime.now().astimezone()

        for entry in log_entries:
            if since_days is not None:
                if entry["datetime"] < now - timedelta(days=since_days):
                    continue

            author = entry["author_name"]
            stats[author] = stats.get(author, 0) + 1

        return sorted(stats.items(), key=lambda x: x[1], reverse=True)

    def commit_statistics(
        self,
        since_days: int | None = None,
    ) -> List[Tuple[str, int]]:
        """
        Returns aggregated commit counts per author.
        """
        log_entries = self.storage.log()
        return self._aggregate_commits(log_entries, since_days)
