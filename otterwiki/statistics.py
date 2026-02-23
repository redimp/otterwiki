from datetime import datetime, timedelta
from typing import List, Tuple

from otterwiki.gitstorage import GitStorage


class StatisticsService:
    def __init__(self, repository_path: str, top_limit: int = 10):
        self.storage = GitStorage(repository_path)
        self.top_limit = top_limit

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

        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

        # If within limit, return directly
        if len(sorted_stats) <= self.top_limit:
            return sorted_stats

        top_entries = sorted_stats[: self.top_limit]
        remainder = sorted_stats[self.top_limit :]

        others_count = sum(count for _, count in remainder)

        top_entries.append(("Others", others_count))

        return top_entries

    def commit_statistics(
        self,
        since_days: int | None = None,
    ) -> List[Tuple[str, int]]:
        """
        Returns aggregated commit counts per author.
        Only top contributors are shown; remainder grouped as 'Others'.
        """
        log_entries = self.storage.log()
        return self._aggregate_commits(log_entries, since_days)
