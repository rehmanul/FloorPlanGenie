import uuid
import json
from PIL import Image
import os

class PlanProcessor:
    def __init__(self):
        self.plans = {}

    def process_plan(self, filepath):
        # Generate unique plan ID
        plan_id = str(uuid.uuid4())

        # Basic plan processing - for now, extract basic info
        plan_data = {
            'id': plan_id,
            'filepath': filepath,
            'dimensions': {'width': 20, 'height': 15},  # Default dimensions in meters
            'walls': [
                {'start': [0, 0], 'end': [20, 0]},
                {'start': [20, 0], 'end': [20, 15]},
                {'start': [20, 15], 'end': [0, 15]},
                {'start': [0, 15], 'end': [0, 0]}
            ],
            'zones': {
                'entry_exit': [{'x': 9, 'y': 0, 'width': 2, 'height': 1}],
                'no_entry': []
            }
        }

        self.plans[plan_id] = plan_data
        return plan_data

    def get_plan_data(self, plan_id):
        return self.plans.get(plan_id)