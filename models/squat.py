from .squat_side import SideSquatAnalyzer
from loguru import logger
class SquatAnalyzer:
    def __init__(self):
        self.side = SideSquatAnalyzer()

    @property
    def counter(self):
        return self.side.counter

    def update_side(self, angle, back_angle, current_time):
        return self.side.update(angle, back_angle, current_time)

    def save_report(self, filename="workout_report.txt"):
        all_reps = self.side.reps_data
        if not all_reps:
            logger.warning("save_report: нет данных для сохранения")
            return
        logger.info(f"Сохраняю отчёт в {filename}")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== АНАЛИЗ ТРЕНИРОВКИ: ПРИСЕДАНИЯ ===\n")
            f.write(f"Всего повторений: {len(all_reps)}\n")
            f.write("=" * 40 + "\n\n")

            for r in all_reps:
                f.write(f"Повтор #{r['rep']} [{r['view']}] | {r['status']} | Время: {r['duration']}с\n")

                if r['view'] == "Side":
                    b_warn = "⚠️" if r['back_fault'] else "✅"
                    f.write(f"  Угол колена: {r['angle']}°\n")
                    f.write(f"  Наклон спины: {r.get('max_back_tilt', 0)}° {b_warn}\n")

                f.write("\n")