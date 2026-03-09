import asyncio
from typing import Optional

from loguru import logger
from openai import AsyncOpenAI


class PerplexityService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client: Optional[AsyncOpenAI] = None
        if api_key:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.perplexity.ai",
            )

    async def _request(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="sonar",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=2000,
                ),
                timeout=10,
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            logger.warning("Perplexity API timeout")
            return None
        except Exception as e:
            logger.error("Perplexity API error: {}", e)
            return None

    async def generate_recipe(self, products: list[str], meal_type: str = "", cuisine: str = "", cook_time: str = "") -> str:
        products_str = ", ".join(products)
        params = []
        if meal_type:
            params.append(f"тип блюда: {meal_type}")
        if cuisine and cuisine != "любая":
            params.append(f"кухня: {cuisine}")
        if cook_time:
            params.append(f"время приготовления: {cook_time}")
        params_str = "; ".join(params) if params else "любое блюдо"

        system_prompt = (
            "Ты - опытный повар-консультант. Отвечай на русском языке. "
            "Предложи один рецепт на основе имеющихся продуктов. "
            "Формат ответа:\n"
            "Название блюда\n\n"
            "Ингредиенты:\n- список с количеством\n\n"
            "Инструкция:\n1. Пошаговая инструкция\n\n"
            "Время приготовления: X минут\n"
            "Примерная калорийность: X ккал на порцию"
        )
        user_prompt = f"Продукты: {products_str}\nПараметры: {params_str}"

        result = await self._request(system_prompt, user_prompt)
        if result:
            return result

        return (
            f"Рецепт из {products_str}\n\n"
            f"К сожалению, AI-ассистент временно недоступен.\n"
            f"Попробуйте позже или используйте имеющиеся продукты для импровизации!"
        )

    async def ask_question(self, question: str) -> str:
        system_prompt = (
            "Ты - помощник по домашнему хозяйству. Отвечай на русском языке. "
            "Давай практичные, конкретные советы."
        )
        result = await self._request(system_prompt, question)
        return result or "AI-ассистент временно недоступен. Попробуйте позже."

    async def generate_report_intro(self, stats: dict) -> str:
        system_prompt = (
            "Ты - веселый семейный ассистент. Отвечай на русском. "
            "Напиши короткое (2-3 предложения) вступление к еженедельному отчету "
            "о домашних делах семьи. Будь позитивным и мотивирующим."
        )
        user_prompt = (
            f"Статистика: выполнено {stats.get('total', 0)} задач, "
            f"приготовлено {stats.get('recipes', 0)} блюд, "
            f"участников: {stats.get('members_count', 0)}"
        )
        result = await self._request(system_prompt, user_prompt)
        return result or "Отличная работа на этой неделе! Продолжайте в том же духе!"

    async def generate_nominations(self, stats: dict) -> str:
        system_prompt = (
            "Ты - ведущий семейной церемонии награждения. Отвечай на русском. "
            "Придумай 3-5 шуточных номинаций для членов семьи на основе статистики. "
            "Используй юмор и теплоту. Примеры номинаций: 'Золотая швабра', 'Железный повар', "
            "'Мастер прокрастинации', 'Невидимка месяца'."
        )
        members_info = []
        for name, data in stats.get("members", {}).items():
            members_info.append(f"{name}: {data.get('chores', 0)} задач, {data.get('recipes', 0)} блюд")
        user_prompt = "Участники:\n" + "\n".join(members_info)
        result = await self._request(system_prompt, user_prompt)

        if result:
            return result

        top = max(stats.get("members", {}).items(), key=lambda x: x[1].get("chores", 0), default=("", {}))
        return f"\"Золотая швабра\" - {top[0]} за максимальный вклад в домашние дела!"

    async def get_improvement_tips(self, task: str) -> str:
        system_prompt = (
            "Ты - эксперт по домашнему хозяйству. Отвечай на русском. "
            "Дай 3-5 практичных советов по выполнению домашней задачи."
        )
        result = await self._request(system_prompt, f"Как лучше выполнить задачу: {task}")
        return result or "AI-ассистент временно недоступен."
