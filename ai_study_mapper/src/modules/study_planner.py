from __future__ import annotations

from typing import Dict, List, Optional

class StudyPlanner:
    """
    Generates a time-based study plan.
    """

    def __init__(self, reading_speed_wpm: int = 150):
        self.reading_speed_wpm = reading_speed_wpm

    def estimate_time(self, text: str) -> int:
        """
        Estimates study time in minutes.
        """
        word_count = len(text.split())
        minutes = max(1, word_count // self.reading_speed_wpm)
        # Add buffer for "studying" vs just "reading" (e.g. 1.5x)
        return int(minutes * 1.5)

    @staticmethod
    def _priority_rank(p: str) -> int:
        return {"High": 3, "Medium": 2, "Low": 1}.get((p or "").title(), 2)

    def create_plan(
        self,
        simplified_text: str,
        available_minutes: int,
        concepts: Dict,
        topics: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Creates a study roadmap.

        - If `topics` is provided, we plan per topic with priority-based scheduling.
        - Otherwise we fall back to naive section splitting (legacy behavior).
        """
        total_estimated_time = self.estimate_time(simplified_text)
        
        plan = {
            "total_estimated_minutes": total_estimated_time,
            "can_finish_today": total_estimated_time <= available_minutes,
            "roadmap": []
        }
        
        # Add a small mental-health-friendly buffer per day (breaks, reset time)
        usable_minutes = max(10, int(available_minutes * 0.85))
        plan["daily_available_minutes"] = available_minutes
        plan["daily_usable_minutes"] = usable_minutes

        if topics:
            # Priority-first ordering, then larger topics first
            items = []
            for t in topics:
                title = t.get("title") or t.get("topic_id") or "Topic"
                pr = (t.get("priority") or "Medium").title()
                # Prefer explicit words estimate from topic clustering; fallback to summary text
                words = int(t.get("estimated_words") or 0)
                if words <= 0:
                    words = len((t.get("summary") or "").split())
                minutes = max(1, int((words / max(1, self.reading_speed_wpm)) * 1.6))  # slightly higher for "study"

                items.append(
                    {
                        "topic": title,
                        "priority": pr,
                        "time_minutes": minutes,
                        "preview": (t.get("summary") or "")[:90].strip() + "...",
                    }
                )

            items.sort(key=lambda x: (self._priority_rank(x["priority"]), x["time_minutes"]), reverse=True)

            current_day = 1
            current_day_time = 0
            day_plan: List[Dict] = []

            for item in items:
                if current_day_time + item["time_minutes"] > usable_minutes and day_plan:
                    plan["roadmap"].append({"day": current_day, "topics": day_plan, "suggestion": "End with a 5–10 min break + quick recap."})
                    current_day += 1
                    current_day_time = 0
                    day_plan = []

                day_plan.append(item)
                current_day_time += item["time_minutes"]

            if day_plan:
                plan["roadmap"].append({"day": current_day, "topics": day_plan, "suggestion": "End with a 5–10 min break + quick recap."})

            plan["planned_topic_count"] = len(items)
            return plan

        # Legacy fallback: section splitting
        sections = [s.strip() for s in simplified_text.split("\n\n") if s.strip()]
        current_day = 1
        current_day_time = 0
        day_plan: List[Dict] = []

        for i, section in enumerate(sections):
            section_time = self.estimate_time(section)

            if current_day_time + section_time > usable_minutes and day_plan:
                plan["roadmap"].append({"day": current_day, "topics": day_plan, "suggestion": "End with a 5–10 min break + quick recap."})
                current_day += 1
                current_day_time = 0
                day_plan = []

            day_plan.append(
                {
                    "topic": f"Section {i+1}",
                    "priority": "Medium",
                    "time_minutes": section_time,
                    "preview": section[:90].strip() + "...",
                }
            )
            current_day_time += section_time

        if day_plan:
            plan["roadmap"].append({"day": current_day, "topics": day_plan, "suggestion": "End with a 5–10 min break + quick recap."})

        return plan

if __name__ == "__main__":
    planner = StudyPlanner()
    text = " ".join(["word"] * 500) # 500 words
    print(f"Estimated time: {planner.estimate_time(text)} mins")
    plan = planner.create_plan(text, 5, {}) # 5 mins available
    print("Plan:", plan)
