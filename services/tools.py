from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import random
import uuid

# Tool definitions for OpenAI function calling
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": "Create a new booking for a service or appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_type": {
                        "type": "string",
                        "description": "Type of service (e.g., 'gym_session', 'personal_training', 'massage', 'consultation')"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date of the booking in YYYY-MM-DD format"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time of the booking in HH:MM format (24-hour)"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration of the booking in minutes",
                        "default": 60
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer"
                    },
                    "customer_email": {
                        "type": "string",
                        "description": "Email of the customer"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes for the booking",
                        "default": ""
                    }
                },
                "required": ["service_type", "date", "time", "customer_name", "customer_email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_booking",
            "description": "Update an existing booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The unique ID of the booking to update"
                    },
                    "date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD format (optional)"
                    },
                    "time": {
                        "type": "string",
                        "description": "New time in HH:MM format (optional)"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "New duration in minutes (optional)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["confirmed", "cancelled", "rescheduled", "completed"],
                        "description": "New status of the booking (optional)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Updated notes (optional)"
                    }
                },
                "required": ["booking_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking",
            "description": "Retrieve booking information",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The unique ID of a specific booking (optional)"
                    },
                    "customer_email": {
                        "type": "string",
                        "description": "Email to search bookings by customer (optional)"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date to filter bookings in YYYY-MM-DD format (optional)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["confirmed", "cancelled", "rescheduled", "completed", "all"],
                        "description": "Filter by booking status (optional)",
                        "default": "all"
                    }
                },
                "required": []
            }
        }
    }
]


class ToolExecutor:
    """Mock implementation of booking tools for demonstration purposes"""
    
    # In-memory storage for mock bookings (in production, use database)
    bookings_db = {}
    
    @classmethod
    def create_booking(cls, service_type: str, date: str, time: str, 
                      customer_name: str, customer_email: str, 
                      duration_minutes: int = 60, notes: str = "") -> Dict[str, Any]:
        """Create a new booking"""
        # In production, this would create a real database entry
        booking_id = str(uuid.uuid4())
        
        booking = {
            "booking_id": booking_id,
            "service_type": service_type,
            "date": date,
            "time": time,
            "duration_minutes": duration_minutes,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "notes": notes,
            "status": "confirmed",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        cls.bookings_db[booking_id] = booking
        
        return {
            "success": True,
            "booking_id": booking_id,
            "message": f"Booking created successfully for {customer_name} on {date} at {time}",
            "booking": booking
        }
    
    @classmethod
    def update_booking(cls, booking_id: str, **kwargs) -> Dict[str, Any]:
        """Update an existing booking"""
        # In production, this would update a real database entry
        if booking_id not in cls.bookings_db:
            return {
                "success": False,
                "error": f"Booking {booking_id} not found"
            }
        
        booking = cls.bookings_db[booking_id]
        updated_fields = []
        
        # Update only provided fields
        for field in ["date", "time", "duration_minutes", "status", "notes"]:
            if field in kwargs and kwargs[field] is not None:
                booking[field] = kwargs[field]
                updated_fields.append(field)
        
        booking["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "booking_id": booking_id,
            "message": f"Booking updated successfully. Updated fields: {', '.join(updated_fields)}",
            "booking": booking
        }
    
    @classmethod
    def get_booking(cls, booking_id: Optional[str] = None, 
                   customer_email: Optional[str] = None,
                   date: Optional[str] = None,
                   status: str = "all") -> Dict[str, Any]:
        """Retrieve booking(s) based on filters"""
        # In production, this would query a real database
        
        # If specific booking ID requested
        if booking_id:
            if booking_id in cls.bookings_db:
                return {
                    "success": True,
                    "booking": cls.bookings_db[booking_id]
                }
            else:
                return {
                    "success": False,
                    "error": f"Booking {booking_id} not found"
                }
        
        # Filter bookings based on criteria
        filtered_bookings = []
        for bid, booking in cls.bookings_db.items():
            match = True
            
            if customer_email and booking["customer_email"] != customer_email:
                match = False
            if date and booking["date"] != date:
                match = False
            if status != "all" and booking["status"] != status:
                match = False
            
            if match:
                filtered_bookings.append(booking)
        
        # If no bookings in database yet, create some mock data
        if not filtered_bookings and not cls.bookings_db:
            # Create sample booking for demo
            sample_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            cls.create_booking(
                service_type="personal_training",
                date=sample_date,
                time="10:00",
                customer_name="John Doe",
                customer_email="john@example.com",
                notes="First session"
            )
            filtered_bookings = list(cls.bookings_db.values())
        
        return {
            "success": True,
            "count": len(filtered_bookings),
            "bookings": filtered_bookings
        }
    
    @classmethod
    def execute_tool(cls, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        tool_map = {
            "create_booking": cls.create_booking,
            "update_booking": cls.update_booking,
            "get_booking": cls.get_booking
        }
        
        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return tool_map[tool_name](**arguments)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}


def format_tool_response(tool_name: str, result: Dict[str, Any]) -> str:
    """Format tool response for inclusion in conversation"""
    if "error" in result:
        return f"[Tool Error: {result['error']}]"
    
    if tool_name == "create_booking":
        if result.get("success"):
            booking = result["booking"]
            return (f"[Booking Created Successfully]\n"
                   f"Booking ID: {booking['booking_id']}\n"
                   f"Customer: {booking['customer_name']}\n"
                   f"Service: {booking['service_type']}\n"
                   f"Date/Time: {booking['date']} at {booking['time']}\n"
                   f"Duration: {booking['duration_minutes']} minutes")
        
    elif tool_name == "update_booking":
        if result.get("success"):
            return f"[Booking Updated Successfully]\n{result['message']}"
    
    elif tool_name == "get_booking":
        if result.get("success"):
            if "booking" in result:  # Single booking
                booking = result["booking"]
                return (f"[Booking Found]\n"
                       f"Booking ID: {booking['booking_id']}\n"
                       f"Customer: {booking['customer_name']}\n"
                       f"Service: {booking['service_type']}\n"
                       f"Date/Time: {booking['date']} at {booking['time']}\n"
                       f"Status: {booking['status']}")
            elif "bookings" in result:  # Multiple bookings
                if result["count"] == 0:
                    return "[No bookings found matching the criteria]"
                bookings_text = f"[Found {result['count']} booking(s)]\n"
                for booking in result["bookings"]:
                    bookings_text += (f"\n• {booking['customer_name']} - "
                                    f"{booking['service_type']} on {booking['date']} at {booking['time']} "
                                    f"(Status: {booking['status']})")
                return bookings_text
    
    return f"[Tool Result: {json.dumps(result, indent=2)}]"