class BaseAnalyzer:
    def __init__(self):
        self.counter = 0
        self.start_time = None
        self.reps_data = []

    def _process_rep_completion(self, min_angle, now):
        self.counter += 1
        duration = round(now - self.start_time, 2) if self.start_time else 0

        if 90 <= min_angle <= 100:
            status = "Perfect"
        elif min_angle < 90:
            status = "Too Deep"
        else:
            status = "Partial"

        return {
            "rep": self.counter,
            "angle": int(min_angle),
            "status": status,
            "duration": duration
        }