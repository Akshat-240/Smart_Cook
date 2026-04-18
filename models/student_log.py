import uuid

class StudentLog:
    def __init__(self ,date ,meal_type,attended):
        self.student_id = str(uuid.uuid4())[:8]
        self.date = date
        # FIRST validate the raw parameter
        if meal_type not in ("breakfast", "lunch", "dinner"):
            raise ValueError("Please Choose the correct meal type")
        # THEN store it — only reaches here if valid
        self.meal_type = meal_type
        if attended not in (True , False) :
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