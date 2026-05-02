from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request, url_for
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from extensions import db
from models.users import PasswordResetToken, User


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _json_error(message, status_code=400):
    return jsonify({'message': message}), status_code


def _is_valid_email(email):
    return isinstance(email, str) and '@' in email and '.' in email and email.strip() == email


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}
    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not full_name:
        return _json_error('Full name is required.', 400)
    if not email or not _is_valid_email(email):
        return _json_error('A valid email address is required.', 400)
    if not password or len(password) < 8:
        return _json_error('Password must be at least 8 characters.', 400)
    if password != confirm_password:
        return _json_error('Password and confirmation must match.', 400)

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return _json_error('Account already exists.', 409)

    user = User(full_name=full_name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Account created successfully.'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    remember_me = bool(data.get('remember_me', False))

    if not email or not password:
        return _json_error('Invalid email or password.', 401)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return _json_error('Invalid email or password.', 401)

    expires = timedelta(days=30) if remember_me else timedelta(days=1)
    access_token = create_access_token(identity=user.id, expires_delta=expires)

    return jsonify({
        'message': 'Login successful.',
        'access_token': access_token,
        'user': user.serialize()
    }), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    if email and _is_valid_email(email):
        user = User.query.filter_by(email=email).first()
        if user:
            reset_request = PasswordResetToken.create(user)
            reset_link = url_for('auth.validate_reset_token', token=reset_request.token, _external=True)
            current_app.logger.info(f'Password reset link generated for {email}: {reset_link}')

    return jsonify({
        'message': 'If the email exists, a password reset link has been sent.'
    }), 200


@auth_bp.route('/reset-password/<string:token>', methods=['GET'])
def validate_reset_token(token):
    reset_request = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_request or not reset_request.is_valid():
        return _json_error('This reset link is invalid or has expired.', 404)

    return jsonify({
        'message': 'Reset link is valid.',
        'email': reset_request.user.email
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get('token') or '').strip()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not token:
        return _json_error('Reset token is required.', 400)
    if not password or len(password) < 8:
        return _json_error('Password must be at least 8 characters.', 400)
    if password != confirm_password:
        return _json_error('Password and confirmation must match.', 400)

    reset_request = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_request or not reset_request.is_valid():
        return _json_error('This reset link is invalid or has expired.', 404)

    user = reset_request.user
    user.set_password(password)
    reset_request.mark_used()
    db.session.commit()

    return jsonify({'message': 'Password has been reset successfully.'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return _json_error('User not found.', 404)
    return jsonify({'user': user.serialize()}), 200
