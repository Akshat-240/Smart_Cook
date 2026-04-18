class MealSession:
    def __init__(self, date ,meal_type ,headcount, event_flag ,cooked_qty ):
        
        self.date = date
        if meal_type not in ("breakfast" ,"lunch","dinner"):
            raise ValueError("Please Choose the correct meal type(breakfast,lunch,dinner)")
        self.meal_type = meal_type
        if headcount < 0 :
            raise ValueError ("Headcount cannot be negative") 
        self.headcount = headcount
        self.event_flag = event_flag
        self.cooked_qty = cooked_qty
    
    def __repr__(self):
        return f"MealSession(date={self.date}, meal_type={self.meal_type}, headcount={self.headcount}, event_flag={self.event_flag}, cooked_qty={self.cooked_qty})"

    def to_dict(self):
        return {
            "date": self.date,
            "meal_type": self.meal_type,
            "headcount": self.headcount,
            "event_flag": self.event_flag,
            "cooked_qty": self.cooked_qty
        }

    @property
    def waste_amount(self):
        return self.cooked_qty - self.headcount 
    
if __name__ == "__main__":
    s = MealSession("2026-04-18", "dinner", 180, False, 45)
    print(s)
    print(s.to_dict())
    print("Waste:", s.waste_amount)