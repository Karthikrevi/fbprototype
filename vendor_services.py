
from database_utils import db_connection
from datetime import datetime, timedelta

class VendorServiceManager:
    """Manage vendor services and bookings efficiently"""
    
    @staticmethod
    def get_vendor_services(vendor_id):
        """Get all services for a vendor"""
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, service_name, description, price, duration_minutes, 
                       category, is_active, created_at, updated_at
                FROM vendor_services 
                WHERE vendor_id = ? AND is_active = 1
                ORDER BY service_name
            """, (vendor_id,))
            return c.fetchall()
    
    @staticmethod
    def add_service(vendor_id, service_name, description, price, duration_minutes, category="General"):
        """Add a new service for vendor"""
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO vendor_services 
                (vendor_id, service_name, description, price, duration_minutes, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vendor_id, service_name, description, price, duration_minutes, category))
            conn.commit()
            return c.lastrowid
    
    @staticmethod
    def update_service(service_id, vendor_id, **kwargs):
        """Update service details"""
        with db_connection() as conn:
            c = conn.cursor()
            
            # Build dynamic update query
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['service_name', 'description', 'price', 'duration_minutes', 'category', 'is_active']:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if update_fields:
                update_fields.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.extend([service_id, vendor_id])
                
                query = f"""
                    UPDATE vendor_services 
                    SET {', '.join(update_fields)}
                    WHERE id = ? AND vendor_id = ?
                """
                c.execute(query, values)
                conn.commit()
                return c.rowcount > 0
        return False
    
    @staticmethod
    def delete_service(service_id, vendor_id):
        """Soft delete a service"""
        return VendorServiceManager.update_service(service_id, vendor_id, is_active=0)
    
    @staticmethod
    def get_available_slots(vendor_id, date, service_duration=60):
        """Get available time slots for a specific date"""
        with db_connection() as conn:
            c = conn.cursor()
            
            # Get vendor time slot settings
            c.execute("""
                SELECT opening_time, closing_time, slot_duration, lunch_break_start, 
                       lunch_break_end, max_groomers, days_of_week
                FROM vendor_time_slots 
                WHERE vendor_id = ? AND is_active = 1
            """, (vendor_id,))
            
            settings = c.fetchone()
            if not settings:
                return VendorServiceManager._get_default_slots()
            
            # Generate time slots based on settings
            slots = VendorServiceManager._generate_time_slots(settings, date)
            
            # Check existing bookings
            c.execute("""
                SELECT time, COUNT(*) as booking_count
                FROM bookings 
                WHERE vendor_id = ? AND date = ? AND status != 'cancelled'
                GROUP BY time
            """, (vendor_id, date))
            
            existing_bookings = dict(c.fetchall())
            max_capacity = settings[5]  # max_groomers
            
            # Filter available slots
            available_slots = []
            for slot in slots:
                current_bookings = existing_bookings.get(slot, 0)
                if current_bookings < max_capacity:
                    available_slots.append({
                        "time": slot,
                        "available": True,
                        "remaining_capacity": max_capacity - current_bookings
                    })
            
            return available_slots
    
    @staticmethod
    def _get_default_slots():
        """Default time slots if no settings configured"""
        return [
            {"time": "09:00", "available": True, "remaining_capacity": 1},
            {"time": "09:30", "available": True, "remaining_capacity": 1},
            {"time": "10:00", "available": True, "remaining_capacity": 1},
            {"time": "10:30", "available": True, "remaining_capacity": 1},
            {"time": "11:00", "available": True, "remaining_capacity": 1},
            {"time": "11:30", "available": True, "remaining_capacity": 1},
            {"time": "14:00", "available": True, "remaining_capacity": 1},
            {"time": "14:30", "available": True, "remaining_capacity": 1},
            {"time": "15:00", "available": True, "remaining_capacity": 1},
            {"time": "15:30", "available": True, "remaining_capacity": 1},
            {"time": "16:00", "available": True, "remaining_capacity": 1},
            {"time": "16:30", "available": True, "remaining_capacity": 1}
        ]
    
    @staticmethod
    def _generate_time_slots(settings, date):
        """Generate time slots based on vendor settings"""
        from datetime import datetime, timedelta
        
        opening_time = datetime.strptime(settings[0], "%H:%M").time()
        closing_time = datetime.strptime(settings[1], "%H:%M").time()
        slot_duration = settings[2]
        lunch_start = datetime.strptime(settings[3], "%H:%M").time() if settings[3] else None
        lunch_end = datetime.strptime(settings[4], "%H:%M").time() if settings[4] else None
        
        # Check if date falls on available day
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_name = date_obj.strftime('%a').lower()
        available_days = settings[6].split(',') if settings[6] else ['mon','tue','wed','thu','fri','sat']
        
        if day_name not in available_days:
            return []
        
        slots = []
        current_time = datetime.combine(date_obj.date(), opening_time)
        end_time = datetime.combine(date_obj.date(), closing_time)
        
        while current_time < end_time:
            slot_time = current_time.time()
            
            # Skip lunch break
            if lunch_start and lunch_end and lunch_start <= slot_time < lunch_end:
                current_time += timedelta(minutes=slot_duration)
                continue
            
            slots.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=slot_duration)
        
        return slots

    @staticmethod
    def create_booking(vendor_id, user_email, service_name, date, time, duration, pet_info):
        """Create a new booking with validation"""
        with db_connection() as conn:
            c = conn.cursor()
            
            # Validate time slot availability
            c.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE vendor_id = ? AND date = ? AND time = ? AND status != 'cancelled'
            """, (vendor_id, date, time))
            
            current_bookings = c.fetchone()[0]
            
            # Get vendor capacity
            c.execute("""
                SELECT max_groomers FROM vendor_time_slots 
                WHERE vendor_id = ? AND is_active = 1
            """, (vendor_id,))
            
            capacity_result = c.fetchone()
            max_capacity = capacity_result[0] if capacity_result else 1
            
            if current_bookings >= max_capacity:
                return {"success": False, "error": "Time slot is fully booked"}
            
            # Create booking
            c.execute("""
                INSERT INTO bookings 
                (vendor_id, user_email, service, date, time, duration, status, 
                 pet_name, pet_parent_name, pet_parent_phone)
                VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?, ?, ?)
            """, (vendor_id, user_email, service_name, date, time, duration,
                  pet_info.get('name', ''), pet_info.get('parent_name', ''), 
                  pet_info.get('parent_phone', '')))
            
            conn.commit()
            booking_id = c.lastrowid
            
            return {"success": True, "booking_id": booking_id}
