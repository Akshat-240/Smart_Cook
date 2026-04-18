import uuid
import datetime

class StudentLog:
    def __init__(self ,date ,meal_type,attended):
        self.student_id = uuid.uuid4().hex
        if isinstance(date, datetime.datetime):
            normalized_date = date.date().isoformat()
        elif isinstance(date, datetime.date):
            normalized_date = date.isoformat()
        elif isinstance(date, str):
            try:
                normalized_date = datetime.date.fromisoformat(date).isoformat()
            except ValueError:
                raise ValueError("date must be a valid ISO YYYY-MM-DD string") from None
        else:
            raise TypeError("date must be a datetime.date, datetime.datetime, or ISO YYYY-MM-DD string")
        self.date = normalized_date
        # FIRST validate the raw parameter
        if meal_type not in ("breakfast", "lunch", "dinner"):
            raise ValueError(
                f"Invalid meal_type '{meal_type}'. Allowed values are: breakfast, lunch, dinner."
            )
        # THEN store it — only reaches here if valid
        self.meal_type = meal_type
        if not isinstance(attended, bool):
            raise ValueError ("Attended is not valid") 
        self.attended = attended


    def __repr__(self):
        return f"StudentLog(student_id = {self.student_id}, date={self.date}, meal_type={self.meal_type}, attended={self.attended})"

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "date": self.date,
            "meal_type": self.meal_type,
            "attended": self.attended,
        }   
    
if __name__ == "__main__":
    s = StudentLog("2026-04-18", "dinner", True)
    print(s)
    print(s.to_dict())