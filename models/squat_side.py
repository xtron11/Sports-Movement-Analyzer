from loguru import logger
from .base import BaseAnalyzer

class SideSquatAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.stage = "up"
        self.min_angle = 180
        self.max_back_tilt = 0

    def update(self, angle, back_angle, current_time):
        if angle < 100 and self.stage == "up":
            self.stage = "down"
            self.start_time = current_time
            self.min_angle = 180
            self.max_back_tilt = 0

        if self.stage == "down":
            self.min_angle = min(self.min_angle, angle)
            if back_angle > self.max_back_tilt:
                self.max_back_tilt = back_angle

        if angle > 160 and self.stage == "down":
            self.stage = "up"
            rep_info = self._process_rep_completion(self.min_angle, current_time)

            rep_info.update({
                "view": "Side",
                "knee_fault": None,
                "max_back_tilt": round(self.max_back_tilt, 1),
                "back_fault": self.max_back_tilt > 50,
            })
            self.reps_data.append(rep_info)
            logger.success(f"Повтор #{self.counter} (Side) | Спина: {self.max_back_tilt:.1f}°")

        return self.counter