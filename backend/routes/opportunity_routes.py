from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.opportunity import Opportunity
from models.users import User


opportunity_bp = Blueprint('opportunity', __name__, url_prefix='/api/opportunities')

ALLOWED_CATEGORIES = ['Technology', 'Business', 'Design', 'Marketing', 'Data Science', 'Other']


def _json_error(message, status_code=400):
    return jsonify({'message': message}), status_code


def _normalize_skills(raw_skills):
    if raw_skills is None:
        return []
    if isinstance(raw_skills, list):
        return [str(skill).strip() for skill in raw_skills if str(skill).strip()]
    value = str(raw_skills or '')
    return [skill.strip() for skill in value.split(',') if skill.strip()]


def _get_current_user():
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    return User.query.get(user_id)


def _validate_request_data(data, require_fields=True):
    errors = []
    name = (data.get('name') or '').strip()
    duration = (data.get('duration') or '').strip()
    start_date = (data.get('start_date') or '').strip()
    description = (data.get('description') or '').strip()
    raw_skills = data.get('skills')
    category = (data.get('category') or '').strip()
    future_opportunities = (data.get('future_opportunities') or '').strip()

    if not name:
        errors.append('Opportunity Name is required.')
    if not duration:
        errors.append('Duration is required.')
    if not start_date:
        errors.append('Start Date is required.')
    if not description:
        errors.append('Description is required.')
    if not raw_skills or len(_normalize_skills(raw_skills)) == 0:
        errors.append('Skills to Gain is required.')
    if not category or category not in ALLOWED_CATEGORIES:
        errors.append('Category is required and must be one of the allowed options.')
    if not future_opportunities:
        errors.append('Future Opportunities is required.')

    return errors


@opportunity_bp.route('/', methods=['GET'])
@jwt_required()
def list_opportunities():
    user = _get_current_user()
    if not user:
        return _json_error('Unauthorized.', 401)

    opportunities = Opportunity.query.filter_by(user_id=user.id).order_by(Opportunity.created_at.desc()).all()
    return jsonify({'opportunities': [opp.serialize() for opp in opportunities]}), 200


@opportunity_bp.route('/', methods=['POST'])
@jwt_required()
def create_opportunity():
    user = _get_current_user()
    if not user:
        return _json_error('Unauthorized.', 401)

    data = request.get_json(silent=True) or {}
    errors = _validate_request_data(data)
    if errors:
        return _json_error(errors, 400)

    skills = _normalize_skills(data.get('skills'))
    max_applicants = data.get('max_applicants')
    parsed_applicants = None
    if max_applicants is not None and str(max_applicants).strip() != '':
        try:
            parsed_applicants = int(max_applicants)
        except ValueError:
            return _json_error('Maximum Applicants must be a valid integer.', 400)

    opportunity = Opportunity(
        user_id=user.id,
        name=data.get('name').strip(),
        duration=data.get('duration').strip(),
        start_date=data.get('start_date').strip(),
        description=data.get('description').strip(),
        skills=','.join(skills),
        category=data.get('category').strip(),
        future_opportunities=data.get('future_opportunities').strip(),
        max_applicants=parsed_applicants,
    )

    db.session.add(opportunity)
    db.session.commit()

    return jsonify({'message': 'Opportunity created successfully.', 'opportunity': opportunity.serialize()}), 201


@opportunity_bp.route('/<int:opportunity_id>', methods=['GET'])
@jwt_required()
def get_opportunity(opportunity_id):
    user = _get_current_user()
    if not user:
        return _json_error('Unauthorized.', 401)

    opportunity = Opportunity.query.filter_by(id=opportunity_id, user_id=user.id).first()
    if not opportunity:
        return _json_error('Opportunity not found.', 404)

    return jsonify({'opportunity': opportunity.serialize()}), 200


@opportunity_bp.route('/<int:opportunity_id>', methods=['PUT'])
@jwt_required()
def update_opportunity(opportunity_id):
    user = _get_current_user()
    if not user:
        return _json_error('Unauthorized.', 401)

    opportunity = Opportunity.query.filter_by(id=opportunity_id, user_id=user.id).first()
    if not opportunity:
        return _json_error('Opportunity not found.', 404)

    data = request.get_json(silent=True) or {}
    errors = _validate_request_data(data)
    if errors:
        return _json_error(errors, 400)

    skills = _normalize_skills(data.get('skills'))
    max_applicants = data.get('max_applicants')
    parsed_applicants = None
    if max_applicants is not None and str(max_applicants).strip() != '':
        try:
            parsed_applicants = int(max_applicants)
        except ValueError:
            return _json_error('Maximum Applicants must be a valid integer.', 400)

    opportunity.name = data.get('name').strip()
    opportunity.duration = data.get('duration').strip()
    opportunity.start_date = data.get('start_date').strip()
    opportunity.description = data.get('description').strip()
    opportunity.skills = ','.join(skills)
    opportunity.category = data.get('category').strip()
    opportunity.future_opportunities = data.get('future_opportunities').strip()
    opportunity.max_applicants = parsed_applicants

    db.session.commit()

    return jsonify({'message': 'Opportunity updated successfully.', 'opportunity': opportunity.serialize()}), 200


@opportunity_bp.route('/<int:opportunity_id>', methods=['DELETE'])
@jwt_required()
def delete_opportunity(opportunity_id):
    user = _get_current_user()
    if not user:
        return _json_error('Unauthorized.', 401)

    opportunity = Opportunity.query.filter_by(id=opportunity_id, user_id=user.id).first()
    if not opportunity:
        return _json_error('Opportunity not found.', 404)

    db.session.delete(opportunity)
    db.session.commit()

    return jsonify({'message': 'Opportunity deleted successfully.'}), 200
