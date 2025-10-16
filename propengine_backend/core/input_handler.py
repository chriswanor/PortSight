from core.property_processor import process_owned_property
from core.potential_processor import process_potential_property

def process_input(data: dict):
    if not isinstance(data, dict):
        return {"input must be a JSON object."}

    file_type = data.get("type")
    if file_type == "owned":
        return process_owned_property(data)
    elif file_type == "potential":
        return process_potential_property(data)
    else:
        return {"error": "JSON must include 'type:  'owned' or 'potential'"}
