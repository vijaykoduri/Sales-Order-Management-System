from flask import Blueprint, jsonify, request
from models import db
from models.notification import Notification
from routes.auth import jwt_required

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query
    if unread_only:
        query = query.filter_by(is_read=False)
        
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notifications]), 200

@notifications_bp.route('/<int:id>/read', methods=['PUT'])
@jwt_required()
def mark_read(id):
    notif = Notification.query.get(id)
    if not notif:
        return jsonify({'message': 'Notification not found'}), 404
        
    notif.is_read = True
    try:
        db.session.commit()
        return jsonify({'message': 'Notification marked as read', 'notification': notif.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update notification', 'error': str(e)}), 500

@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    try:
        unread = Notification.query.filter_by(is_read=False).all()
        for n in unread:
            n.is_read = True
        db.session.commit()
        return jsonify({'message': 'All notifications marked as read', 'count': len(unread)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update notifications', 'error': str(e)}), 500
