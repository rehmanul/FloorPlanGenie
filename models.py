from app import db


class FloorPlan(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    dimensions = db.Column(db.JSON)
    walls_data = db.Column(db.JSON)
    zones_data = db.Column(db.JSON)


class OptimizationResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor_plan_id = db.Column(db.String(50), db.ForeignKey('floor_plan.id'), nullable=False)
    optimization_type = db.Column(db.String(50), nullable=False)
    boxes_data = db.Column(db.JSON)
    corridors_data = db.Column(db.JSON)
    statistics = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    floor_plan = db.relationship('FloorPlan', backref=db.backref('optimizations', lazy=True))