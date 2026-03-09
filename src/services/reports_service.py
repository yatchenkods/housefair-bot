from datetime import datetime, timedelta

from src.database.repository import Database
from src.services.perplexity_service import PerplexityService


class ReportsService:
    def __init__(self, db: Database, perplexity: PerplexityService):
        self.db = db
        self.perplexity = perplexity

    async def calculate_stats(self, family_id: int, since: str) -> dict:
        members = await self.db.get_family_members(family_id)
        chores_stats = await self.db.get_chores_stats(family_id, since)
        recipes_stats = await self.db.get_recipes_stats(family_id, since)

        member_map = {m["id"]: m for m in members}
        chores_by_member = {s["assigned_to"]: s["count"] for s in chores_stats}
        recipes_by_member = {s["cooked_by"]: s["count"] for s in recipes_stats}

        total_chores = sum(chores_by_member.values())
        total_recipes = sum(recipes_by_member.values())

        members_data = {}
        for m in members:
            chore_count = chores_by_member.get(m["id"], 0)
            recipe_count = recipes_by_member.get(m["id"], 0)
            members_data[m["display_name"]] = {
                "chores": chore_count,
                "recipes": recipe_count,
                "pct": round(chore_count / total_chores * 100) if total_chores > 0 else 0,
            }

        return {
            "total": total_chores,
            "recipes": total_recipes,
            "members_count": len(members),
            "members": members_data,
        }

    async def format_weekly_report(self, family_id: int) -> str:
        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        stats = await self.calculate_stats(family_id, since)

        intro = await self.perplexity.generate_report_intro(stats)
        popular = await self.db.get_popular_chores(family_id, since)
        overdue = await self.db.get_overdue_count(family_id)

        now = datetime.utcnow()
        week_start = (now - timedelta(days=7)).strftime("%d.%m")
        week_end = now.strftime("%d.%m.%Y")

        lines = [f"Отчет за неделю {week_start}-{week_end}\n"]
        lines.append(intro)
        lines.append(f"\nВсего выполнено задач: {stats['total']}")
        lines.append(f"Приготовлено блюд: {stats['recipes']}\n")
        lines.append("Вклад участников:")

        max_chores = max((d["chores"] for d in stats["members"].values()), default=1) or 1
        for name, data in sorted(stats["members"].items(), key=lambda x: -x[1]["chores"]):
            bar_len = int(data["chores"] / max_chores * 10)
            bar = "\u2588" * bar_len
            lines.append(f"  {name} - {data['chores']} ({data['pct']}%) {bar}")

        if popular:
            lines.append("\nПопулярные задачи:")
            for p in popular:
                lines.append(f"  {p['title']} - {p['count']} раз")

        if overdue > 0:
            lines.append(f"\nНевыполненных задач: {overdue}")

        return "\n".join(lines)

    async def format_monthly_report(self, family_id: int) -> str:
        since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        stats = await self.calculate_stats(family_id, since)

        prev_since = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d")
        prev_until = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        prev_stats = await self.calculate_stats(family_id, prev_since)

        nominations = await self.perplexity.generate_nominations(stats)

        now = datetime.utcnow()
        lines = [f"Ежемесячный отчет за {now.strftime('%B %Y')}\n"]
        lines.append(f"Выполнено задач: {stats['total']}")

        if prev_stats["total"] > 0:
            diff = stats["total"] - prev_stats["total"]
            pct = round(diff / prev_stats["total"] * 100)
            direction = "больше" if diff >= 0 else "меньше"
            lines.append(f"Это на {abs(pct)}% {direction}, чем в прошлом месяце.")

        lines.append(f"Приготовлено блюд: {stats['recipes']}\n")
        lines.append("Детальная статистика:")

        max_chores = max((d["chores"] for d in stats["members"].values()), default=1) or 1
        for name, data in sorted(stats["members"].items(), key=lambda x: -x[1]["chores"]):
            bar_len = int(data["chores"] / max_chores * 15)
            bar = "\u2588" * bar_len
            lines.append(f"  {name}: {data['chores']} задач, {data['recipes']} блюд")
            lines.append(f"    {bar} {data['pct']}%")

        lines.append(f"\nНоминации:\n{nominations}")

        return "\n".join(lines)

    async def format_personal_stats(self, family_id: int, member_id: int, member_name: str) -> str:
        since_week = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        since_month = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

        week_chores = await self.db.get_chores_stats(family_id, since_week)
        month_chores = await self.db.get_chores_stats(family_id, since_month)

        week_count = next((s["count"] for s in week_chores if s["assigned_to"] == member_id), 0)
        month_count = next((s["count"] for s in month_chores if s["assigned_to"] == member_id), 0)

        week_recipes = await self.db.get_recipes_stats(family_id, since_week)
        month_recipes = await self.db.get_recipes_stats(family_id, since_month)
        week_recipe_count = next((s["count"] for s in week_recipes if s["cooked_by"] == member_id), 0)
        month_recipe_count = next((s["count"] for s in month_recipes if s["cooked_by"] == member_id), 0)

        return (
            f"Статистика {member_name}:\n\n"
            f"За неделю:\n"
            f"  Задач выполнено: {week_count}\n"
            f"  Блюд приготовлено: {week_recipe_count}\n\n"
            f"За месяц:\n"
            f"  Задач выполнено: {month_count}\n"
            f"  Блюд приготовлено: {month_recipe_count}"
        )

    async def build_leaderboard(self, family_id: int) -> str:
        since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        stats = await self.calculate_stats(family_id, since)

        sorted_members = sorted(stats["members"].items(), key=lambda x: -x[1]["chores"])

        lines = ["Таблица лидеров (за месяц):\n"]
        medals = ["1.", "2.", "3."]
        for i, (name, data) in enumerate(sorted_members):
            prefix = medals[i] if i < 3 else f"{i + 1}."
            lines.append(f"{prefix} {name} - {data['chores']} задач, {data['recipes']} блюд")

        return "\n".join(lines)
