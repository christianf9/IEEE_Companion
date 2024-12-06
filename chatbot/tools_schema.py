# tools_schema.py

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_tutors",
            "description": "Get information about tutors, their classes, and schedules. Can filter by class code, day, or tutor name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_code": {
                        "type": "string",
                        "description": "Filter by class code (e.g., 'EE1001')"
                    },
                    "day": {
                        "type": "string",
                        "description": "Filter by day of the week",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "tutor_name": {
                        "type": "string",
                        "description": "Filter by tutor name"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_tutor",
            "description": "Add a new tutor to the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "tutor_name": {
                        "type": "string",
                        "description": "Name of the new tutor"
                    },
                    "class_code": {
                        "type": "string",
                        "description": "Class code (e.g., 'EE1001')"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "Class name"
                    },
                    "day": {
                        "type": "string",
                        "description": "Day of the week",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in HH:MM format"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in HH:MM format"
                    }
                },
                "required": ["tutor_name", "class_code", "class_name", "day", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_tutor",
            "description": "Remove a tutor from the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "tutor_name": {
                        "type": "string",
                        "description": "Name of the tutor to remove"
                    }
                },
                "required": ["tutor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_tutor_info",
            "description": "Update a tutor's information including schedule and class details",
            "parameters": {
                "type": "object",
                "properties": {
                    "tutor_name": {
                        "type": "string",
                        "description": "Name of the tutor to update"
                    },
                    "new_class_code": {
                        "type": "string",
                        "description": "New class code"
                    },
                    "new_class_name": {
                        "type": "string",
                        "description": "New class name"
                    },
                    "new_day": {
                        "type": "string",
                        "description": "New day of the week",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "new_start_time": {
                        "type": "string",
                        "description": "New start time in HH:MM format"
                    },
                    "new_end_time": {
                        "type": "string",
                        "description": "New end time in HH:MM format"
                    }
                },
                "required": ["tutor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_tutor_update",
            "description": "Validate and store pending tutor updates, tracking what information is still needed",
            "parameters": {
                "type": "object",
                "properties": {
                    "update_type": {
                        "type": "string",
                        "description": "Type of update being made",
                        "enum": ["schedule", "class", "name", "both"]
                    },
                    "tutor_name": {
                        "type": "string",
                        "description": "Current name of the tutor to update"
                    },
                    "partial_info": {
                        "type": "object",
                        "description": "Partial information provided by the user",
                        "properties": {
                            "new_tutor_name": {"type": "string", "description": "The new name of the tutor"},
                            "new_class_code": {"type": "string", "description": "The new class code to update"},
                            "new_class_name": {"type": "string", "description": "The new class name to update"},
                            "new_day": {"type": "string", "description": "The new day of the schedule"},
                            "new_start_time": {
                                "type": "string",
                                "description": "The new start time in HH:MM format"
                            },
                            "new_end_time": {
                                "type": "string",
                                "description": "The new end time in HH:MM format"
                            }
                        },
                        "required": []
                    }
                },
                "required": ["update_type"]
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "Get information about club events. Can filter by name or day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_name": {
                        "type": "string",
                        "description": "Filter by event name"
                    },
                    "day": {
                        "type": "string",
                        "description": "Filter by day of the week",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_event",
            "description": "Add a new event to the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_name": {
                        "type": "string",
                        "description": "Name of the event"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the event"
                    },
                    "day": {
                        "type": "string",
                        "description": "Day of the week",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in HH:MM format"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in HH:MM format"
                    }
                },
                "required": ["event_name", "description", "day", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_event",
            "description": "Update an event's information",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_name": {
                        "type": "string",
                        "description": "Current name of the event to update"
                    },
                    "new_event_name": {
                        "type": "string",
                        "description": "New name for the event"
                    },
                    "new_description": {
                        "type": "string",
                        "description": "New description for the event"
                    },
                    "new_day": {
                        "type": "string",
                        "description": "New day of the week",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "new_start_time": {
                        "type": "string",
                        "description": "New start time in HH:MM format"
                    },
                    "new_end_time": {
                        "type": "string",
                        "description": "New end time in HH:MM format"
                    }
                },
                "required": ["event_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_event",
            "description": "Remove an event from the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_name": {
                        "type": "string",
                        "description": "Name of the event to remove"
                    }
                },
                "required": ["event_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rules",
            "description": "Get all club rules",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_rule",
            "description": "Add a new rule to the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the rule"
                    }
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_rule",
            "description": "Remove a rule from the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the rule to remove"
                    }
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "instagram_post",
            "description": "Post an image to Instagram with a caption.",
            "parameters": {
                "type": "object",
                "properties": {
                    "caption": {
                        "type": "string",
                        "description": "The caption to include with the Instagram post."
                    }
                },
                "required": ["caption"]
            }
        }
    }
]