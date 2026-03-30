
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..extensions import db


class AuditLog(db.Model):
    """Audit log model for tracking sensitive operations"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    
    # Actor information
    user_id = Column(Integer, ForeignKey('users.id'))
    user_email = Column(String(255))  # Stored for historical purposes
    user_role = Column(String(100))
    session_id = Column(String(255))
    
    # Action details
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100))  # user, pet, document, etc.
    resource_id = Column(String(100))
    resource_identifier = Column(String(500))  # human-readable identifier
    
    # Operation details
    operation_type = Column(String(50))  # CREATE, READ, UPDATE, DELETE, LOGIN, etc.
    api_endpoint = Column(String(500))
    http_method = Column(String(10))
    
    # Request context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))
    
    # Changes tracking (for UPDATE operations)
    old_values = Column(Text)  # JSON of old values
    new_values = Column(Text)  # JSON of new values
    changed_fields = Column(Text)  # JSON array of changed field names
    
    # Outcome
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    response_code = Column(Integer)
    
    # Additional context
    business_context = Column(Text)
    compliance_note = Column(Text)
    tags = Column(Text)  # JSON array of tags for categorization
    
    # Risk assessment
    risk_level = Column(String(20), default='low')  # low, medium, high, critical
    sensitive_data_accessed = Column(Boolean, default=False)
    
    # Retention
    retention_days = Column(Integer, default=2555)  # 7 years default
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_email or "Anonymous"}>'
    
    @classmethod
    def log_action(cls, user_id=None, user_email=None, action=None, resource_type=None, 
                   resource_id=None, operation_type=None, success=True, **kwargs):
        """Helper method to create audit log entries"""
        log_entry = cls(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            operation_type=operation_type,
            success=success,
            **kwargs
        )
        
        db.session.add(log_entry)
        return log_entry
    
    @classmethod
    def log_login_attempt(cls, email, success, ip_address=None, user_agent=None, error_message=None):
        """Log login attempts"""
        return cls.log_action(
            user_email=email,
            action='LOGIN_ATTEMPT',
            operation_type='LOGIN',
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
            risk_level='medium' if not success else 'low'
        )
    
    @classmethod
    def log_data_access(cls, user_id, user_email, resource_type, resource_id, 
                       sensitive_data=False, **kwargs):
        """Log access to sensitive data"""
        return cls.log_action(
            user_id=user_id,
            user_email=user_email,
            action=f'ACCESS_{resource_type.upper()}',
            resource_type=resource_type,
            resource_id=resource_id,
            operation_type='READ',
            sensitive_data_accessed=sensitive_data,
            risk_level='medium' if sensitive_data else 'low',
            **kwargs
        )
    
    @classmethod
    def log_data_modification(cls, user_id, user_email, resource_type, resource_id, 
                             old_values=None, new_values=None, **kwargs):
        """Log data modifications"""
        import json
        
        # Calculate changed fields
        changed_fields = []
        if old_values and new_values:
            for key in new_values:
                if key in old_values and old_values[key] != new_values[key]:
                    changed_fields.append(key)
        
        return cls.log_action(
            user_id=user_id,
            user_email=user_email,
            action=f'MODIFY_{resource_type.upper()}',
            resource_type=resource_type,
            resource_id=resource_id,
            operation_type='UPDATE',
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            changed_fields=json.dumps(changed_fields) if changed_fields else None,
            risk_level='medium',
            **kwargs
        )
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'user_role': self.user_role,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'resource_identifier': self.resource_identifier,
            'operation_type': self.operation_type,
            'ip_address': self.ip_address,
            'success': self.success,
            'error_message': self.error_message,
            'response_code': self.response_code,
            'risk_level': self.risk_level,
            'sensitive_data_accessed': self.sensitive_data_accessed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
