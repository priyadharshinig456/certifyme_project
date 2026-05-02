from datetime import datetime

from extensions import db


class Opportunity(db.Model):
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    duration = db.Column(db.String(80), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, nullable=False)
    future_opportunities = db.Column(db.Text, nullable=False)
    max_applicants = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = db.relationship('User', back_populates='opportunities')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'duration': self.duration,
            'start_date': self.start_date,
            'description': self.description,
            'skills': [skill.strip() for skill in self.skills.split(',') if skill.strip()],
            'future_opportunities': self.future_opportunities,
            'max_applicants': self.max_applicants,
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z'
        }
