# tools_functions.py

from datetime import datetime
from typing import Optional, Dict, Any, List
import threading
from instagrapi import Client as instaClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

INSTAGRAM_USER = os.getenv("INSTAGRAM_USER")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Initialize state storage
pending_updates: Dict[str, Dict[str, Any]] = {}
lock = threading.Lock()

def validate_time_format(time_str):
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def validate_day(day):
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return day in valid_days

def get_tutors(tutors_collection, class_code=None, day=None, tutor_name=None):
    query = {}
    if class_code:
        query["class_code"] = class_code
    if day:
        query["day"] = day
    if tutor_name:
        query["tutor_name"] = {"$regex": tutor_name, "$options": "i"}
    
    try:
        tutors = list(tutors_collection.find(query))
        for tutor in tutors:
            tutor['_id'] = str(tutor['_id'])
        
        if not tutors:
            return "No tutors found matching your criteria."
        
        response = "Here are the tutors matching your criteria:\n\n"
        for tutor in tutors:
            response += (f"Tutor: {tutor['tutor_name']}\n"
                        f"Class: {tutor['class_name']} ({tutor['class_code']})\n"
                        f"Schedule: {tutor['day']} {tutor['start_time']} - {tutor['end_time']}\n\n")
        return response
    except Exception as e:
        return f"Error retrieving tutors: {str(e)}"

def add_tutor(tutors_collection, tutor_name, class_code, class_name, day, start_time, end_time):
    try:
        # Check if tutor already exists
        if tutors_collection.find_one({"tutor_name": tutor_name}):
            return f"A tutor with the name {tutor_name} already exists."
        
        # Validate inputs
        if not validate_day(day):
            return "Invalid day."
        if not validate_time_format(start_time):
            return "Invalid start time format. Please use HH:MM format."
        if not validate_time_format(end_time):
            return "Invalid end time format. Please use HH:MM format."
        
        # Create new tutor document
        new_tutor = {
            "tutor_name": tutor_name,
            "class_code": class_code,
            "class_name": class_name,
            "day": day,
            "start_time": start_time,
            "end_time": end_time
        }
        
        # Insert into database
        result = tutors_collection.insert_one(new_tutor)
        
        if result.inserted_id:
            return (f"Successfully added tutor {tutor_name}:\n"
                   f"Class: {class_name} ({class_code})\n"
                   f"Schedule: {day} {start_time} - {end_time}")
        else:
            return "Failed to add tutor."
            
    except Exception as e:
        return f"Error adding tutor: {str(e)}"

def remove_tutor(tutors_collection, tutor_name):
    try:
        # Check if tutor exists
        if not tutors_collection.find_one({"tutor_name": tutor_name}):
            return f"No tutor found with name: {tutor_name}"
        
        # Remove tutor
        result = tutors_collection.delete_one({"tutor_name": tutor_name})
        
        if result.deleted_count > 0:
            return f"Successfully removed tutor: {tutor_name}"
        else:
            return "Failed to remove tutor."
            
    except Exception as e:
        return f"Error removing tutor: {str(e)}"

# Update the existing update_tutor_info function to handle name changes
def update_tutor_info(tutors_collection, tutor_name, new_tutor_name=None, new_class_code=None, new_class_name=None, new_day=None, new_start_time=None, new_end_time=None):
    try:
        # Check if tutor exists
        tutor = tutors_collection.find_one({"tutor_name": tutor_name})
        if not tutor:
            return f"No tutor found with name: {tutor_name}"
        
        # Prepare update data
        update_data = {}
        
        # Handle name change first if provided
        if new_tutor_name and new_tutor_name != tutor_name:
            # Check if new name already exists
            if tutors_collection.find_one({"tutor_name": new_tutor_name}):
                return f"Cannot update name: A tutor with the name {new_tutor_name} already exists."
            update_data["tutor_name"] = new_tutor_name
        
        # Add other updates
        if new_class_code:
            update_data["class_code"] = new_class_code
        if new_class_name:
            update_data["class_name"] = new_class_name
        if new_day:
            if not validate_day(new_day):
                return "Invalid day. Must be Monday through Friday."
            update_data["day"] = new_day
        if new_start_time:
            if not validate_time_format(new_start_time):
                return "Invalid start time format. Please use HH:MM format."
            update_data["start_time"] = new_start_time
        if new_end_time:
            if not validate_time_format(new_end_time):
                return "Invalid end time format. Please use HH:MM format."
            update_data["end_time"] = new_end_time
        
        # Perform update
        result = tutors_collection.update_one(
            {"tutor_name": tutor_name},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return "No changes were made to the tutor's information."
        
        # Get updated tutor info (using new name if it was changed)
        updated_tutor = tutors_collection.find_one(
            {"tutor_name": new_tutor_name if new_tutor_name else tutor_name}
        )
        
        return (f"Successfully updated tutor information:\n"
                f"Tutor: {updated_tutor['tutor_name']}\n"
                f"Class: {updated_tutor['class_name']} ({updated_tutor['class_code']})\n"
                f"Schedule: {updated_tutor['day']} {updated_tutor['start_time']} - {updated_tutor['end_time']}")
        
    except Exception as e:
        return f"Error updating tutor information: {str(e)}"
    
def validate_tutor_update(tutors_collection, session_id, update_type, tutor_name=None, partial_info=None):
    with lock:
        print("Validating tutor update")
        if session_id not in pending_updates:
            pending_updates[session_id] = {"update_type": update_type, "info": {}}
        
        update_state = pending_updates[session_id]
        
        if tutor_name:
            # Verify tutor exists
            tutor = tutors_collection.find_one({"tutor_name": tutor_name})
            if not tutor:
                return f"No tutor found with name: {tutor_name}. Please provide a valid tutor name."
            update_state["tutor_name"] = tutor_name

        if partial_info:
            update_state["info"].update(partial_info)
        
        # Check what information is still needed
        missing_info = []
        
        if "tutor_name" not in update_state:
            missing_info.append("tutor name")
        
        # Handle different types of updates
        if update_type == "name":
            if not update_state["info"].get("new_tutor_name"):
                missing_info.append("new tutor name")
        
        elif update_type == "class":
            # Allow updating either code or name independently
            if not any([
                update_state["info"].get("new_class_code"),
                update_state["info"].get("new_class_name")
            ]):
                missing_info.append("either class code or class name")
        
        elif update_type == "schedule":
            # Allow updating individual schedule components
            if not any([
                update_state["info"].get("new_day"),
                update_state["info"].get("new_start_time"),
                update_state["info"].get("new_end_time")
            ]):
                missing_info.append("day, start time, or end time")
        
        elif update_type == "both":
            # Check for at least one class update and one schedule update
            has_class_update = any([
                update_state["info"].get("new_class_code"),
                update_state["info"].get("new_class_name")
            ])
            has_schedule_update = any([
                update_state["info"].get("new_day"),
                update_state["info"].get("new_start_time"),
                update_state["info"].get("new_end_time")
            ])
            
            if not has_class_update:
                missing_info.append("class code or name")
            if not has_schedule_update:
                missing_info.append("schedule information (day, start time, or end time)")
        
        if missing_info:
            return f"I still need the following information: {', '.join(missing_info)}"
        
        # Validate any provided times
        if update_state["info"].get("new_start_time"):
            if not validate_time_format(update_state["info"]["new_start_time"]):
                return "Invalid start time format. Please use HH:MM format."
                
        if update_state["info"].get("new_end_time"):
            if not validate_time_format(update_state["info"]["new_end_time"]):
                return "Invalid end time format. Please use HH:MM format."
        
        # All information is complete, proceed with update
        result = update_tutor_info(
            tutors_collection,
            update_state["tutor_name"],
            **update_state["info"]
        )
        
        # Clear the pending update
        del pending_updates[session_id]
        
        return result
    
def get_events(events_collection, event_name=None, day=None):
    query = {}
    if event_name:
        query["event_name"] = {"$regex": event_name, "$options": "i"}
    if day:
        query["day"] = day
    
    try:
        events = list(events_collection.find(query))
        
        if not events:
            return "No events found matching your criteria."
        
        response = "Here are the events matching your criteria:\n\n"
        for event in events:
            response += (f"Event: {event['event_name']}\n"
                        f"Description: {event['description']}\n"
                        f"Schedule: {event['day']} {event['start_time']} - {event['end_time']}\n\n")
        return response
    except Exception as e:
        return f"Error retrieving events: {str(e)}"

def add_event(events_collection, event_name, description, day, start_time, end_time):
    try:
        # Check if event already exists
        if events_collection.find_one({"event_name": event_name}):
            return f"An event with the name {event_name} already exists."
        
        # Validate inputs
        if not validate_day(day):
            return "Invalid day. Must be Monday through Friday."
        if not validate_time_format(start_time):
            return "Invalid start time format. Please use HH:MM format."
        if not validate_time_format(end_time):
            return "Invalid end time format. Please use HH:MM format."
        
        # Create new event document
        new_event = {
            "event_name": event_name,
            "description": description,
            "day": day,
            "start_time": start_time,
            "end_time": end_time
        }
        
        # Insert into database
        result = events_collection.insert_one(new_event)
        
        if result.inserted_id:
            return (f"Successfully added event {event_name}:\n"
                   f"Description: {description}\n"
                   f"Schedule: {day} {start_time} - {end_time}")
        else:
            return "Failed to add event."
            
    except Exception as e:
        return f"Error adding event: {str(e)}"

def update_event(events_collection, event_name, new_event_name=None, new_description=None, new_day=None, new_start_time=None, new_end_time=None):
    try:
        # Check if event exists
        event = events_collection.find_one({"event_name": event_name})
        if not event:
            return f"No event found with name: {event_name}"
        
        # Prepare update data
        update_data = {}
        
        if new_event_name and new_event_name != event_name:
            if events_collection.find_one({"event_name": new_event_name}):
                return f"Cannot update name: An event with the name {new_event_name} already exists."
            update_data["event_name"] = new_event_name
        
        if new_description:
            update_data["description"] = new_description
        
        if new_day:
            if not validate_day(new_day):
                return "Invalid day. Must be Monday through Friday."
            update_data["day"] = new_day
            
        if new_start_time:
            if not validate_time_format(new_start_time):
                return "Invalid start time format. Please use HH:MM format."
            update_data["start_time"] = new_start_time
            
        if new_end_time:
            if not validate_time_format(new_end_time):
                return "Invalid end time format. Please use HH:MM format."
            update_data["end_time"] = new_end_time
        
        if not update_data:
            return "No changes provided for update."
        
        # Perform update
        result = events_collection.update_one(
            {"event_name": event_name},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return "No changes were made to the event."
        
        # Get updated event info
        updated_event = events_collection.find_one(
            {"event_name": new_event_name if new_event_name else event_name}
        )
        
        return (f"Successfully updated event information:\n"
                f"Event: {updated_event['event_name']}\n"
                f"Description: {updated_event['description']}\n"
                f"Schedule: {updated_event['day']} {updated_event['start_time']} - {updated_event['end_time']}")
        
    except Exception as e:
        return f"Error updating event: {str(e)}"

def remove_event(events_collection, event_name):
    try:
        # Check if event exists
        if not events_collection.find_one({"event_name": event_name}):
            return f"No event found with name: {event_name}"
        
        # Remove event
        result = events_collection.delete_one({"event_name": event_name})
        
        if result.deleted_count > 0:
            return f"Successfully removed event: {event_name}"
        else:
            return "Failed to remove event."
            
    except Exception as e:
        return f"Error removing event: {str(e)}"

def get_rules(rules_collection):
    try:
        rules = list(rules_collection.find())
        
        if not rules:
            return "No rules found."
        
        response = "Club Rules:\n\n"
        for i, rule in enumerate(rules, 1):
            response += f"{i}. {rule['description']}\n"
        return response
    except Exception as e:
        return f"Error retrieving rules: {str(e)}"

def add_rule(rules_collection, description):
    try:
        # Check if rule already exists
        if rules_collection.find_one({"description": description}):
            return "This rule already exists."
        
        # Create new rule document
        new_rule = {"description": description}
        
        # Insert into database
        result = rules_collection.insert_one(new_rule)
        
        if result.inserted_id:
            return f"Successfully added new rule: {description}"
        else:
            return "Failed to add rule."
            
    except Exception as e:
        return f"Error adding rule: {str(e)}"

def remove_rule(rules_collection, description):
    try:
        # Check if rule exists
        if not rules_collection.find_one({"description": description}):
            return "Rule not found."
        
        # Remove rule
        result = rules_collection.delete_one({"description": description})
        
        if result.deleted_count > 0:
            return f"Successfully removed rule: {description}"
        else:
            return "Failed to remove rule."
            
    except Exception as e:
        return f"Error removing rule: {str(e)}"
    
def instagram_post(session_id, caption):
    try:
        UPLOAD_FOLDER = "./uploads"

        # get the image path based on the session_id and contains _image doesnt matter the extension
        image_path = os.path.join(UPLOAD_FOLDER, [f for f in os.listdir(UPLOAD_FOLDER) if f"{session_id}_image" in f][0])

        # if no image found return no image found
        if not image_path:
            return "No image found. Upload an image first."

        insta_client = instaClient()
        insta_client.login(INSTAGRAM_USER, INSTAGRAM_PASSWORD)

        # Upload the image
        media = insta_client.photo_upload(
            image_path,
            caption,
            extra_data={
                "custom_accessibility_caption": "alt text example",
                "like_and_view_counts_disabled": 1,
                "disable_comments": 1,
            }
        )
        print("Photo uploaded with id:", media.dict()["id"], "and caption:", caption)
        return f"Photo sucsessfully uploaded with caption: {caption}"
    except Exception as e:
        return f"Error uploading photo: {str(e)}"

def check_privilege(session_id, admin_ids, function_name):
    if session_id in admin_ids:
        print("ALLOWED")
        return (True, "")
    else:
        print("DENIED")
        return (False, f"User does not have permission to execute {function_name}. Ask to enter password or to only query tutors, events, rules or ask questions.")

# Update handle_tool_call
def handle_tool_call(tutors_collection, rules_collection, events_collection, function_name, function_args, session_id, admin_ids):
    # print function name and all function arguments
    print(f"Function: {function_name}")
    print(f"Args: {function_args}")
    try:
        if function_name == "get_tutors":
            return get_tutors(tutors_collection, **function_args)
        
        elif function_name == "add_tutor":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return add_tutor(tutors_collection, **function_args)
            else:
                return check[1]
            
        elif function_name == "remove_tutor":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return remove_tutor(tutors_collection, **function_args)
            else:
                return check[1]
        
        elif function_name == "update_tutor_info":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return update_tutor_info(tutors_collection, **function_args)
            else:
                return check[1]
        
        elif function_name == "validate_tutor_update":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return validate_tutor_update(tutors_collection, session_id, **function_args)
            else:
                return check[1]
        
        elif function_name == "get_events":
            return get_events(events_collection, **function_args)
        
        elif function_name == "add_event":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return add_event(events_collection, **function_args)
            else:
                return check[1]
        
        elif function_name == "update_event":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return update_event(events_collection, **function_args)
            else:
                return check[1]
        
        elif function_name == "remove_event":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return remove_event(events_collection, **function_args)
            else:
                return check[1]
        
        elif function_name == "get_rules":
            return get_rules(rules_collection)
        
        elif function_name == "add_rule":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return add_rule(rules_collection, **function_args)
            else:
                return check[1]
        
        elif function_name == "remove_rule":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return remove_rule(rules_collection, **function_args)
            else:
                return check[1]
        
        elif function_name == "instagram_post":
            check = check_privilege(session_id, admin_ids, function_name)
            if check[0]:
                return instagram_post(session_id, **function_args)
            else:
                return check[1]
        
        else:
            return f"Unknown function: {function_name}"
    except Exception as e:
        return f"Error executing {function_name}: {str(e)}"