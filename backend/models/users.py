import uuid
from datetime import datetime, timedelta

from extensions import bcrypt, db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    opportunities = db.relationship('Opportunity', back_populates='owner', cascade='all, delete-orphan')

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def serialize(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'created_at': self.created_at.isoformat() + 'Z'
        }


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='password_reset_tokens')

    @classmethod
    def create(cls, user):
        token = uuid.uuid4().hex
        expires_at = datetime.utcnow() + timedelta(hours=1)
        instance = cls(user_id=user.id, token=token, expires_at=expires_at)
        db.session.add(instance)
        db.session.commit()
        return instance

    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at

    def mark_used(self):
        self.used = True
        db.session.commit()
