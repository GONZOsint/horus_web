from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
from app import db

# Tabla de asociación para la relación many-to-many entre User y Team
team_members = db.Table('team_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    invitation_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    solved_flags = db.Column(db.Integer, default=0)
    creator = db.relationship('User', 
                            foreign_keys=[created_by],
                            backref=db.backref('created_teams', lazy=True))
    members = db.relationship('User', 
                            secondary=team_members, 
                            lazy='subquery',
                            backref=db.backref('teams', lazy=True))

    def __init__(self, **kwargs):
        super(Team, self).__init__(**kwargs)
        self.invitation_code = self.generate_invitation_code()
        self.points = 0
        self.solved_flags = 0

    def update_points(self):
        """Update team points based on correct flag submissions"""
        correct_submissions = FlagSubmission.query.filter_by(
            team_id=self.id,
            is_correct=True
        ).all()
        self.points = sum(sub.points for sub in correct_submissions)
        self.solved_flags = len(correct_submissions)
        db.session.commit()

    def generate_invitation_code(self):
        """Generate a unique 8-character invitation code"""
        while True:
            code = secrets.token_urlsafe(6)[:8].upper()
            if not Team.query.filter_by(invitation_code=code).first():
                return code

    def __repr__(self):
        return f'<Team {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_judge = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    login_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    current_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    current_team = db.relationship('Team', 
                                 foreign_keys=[current_team_id],
                                 backref=db.backref('active_members', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_login_info(self):
        """Update user's login information"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()

    def get_id(self):
        """Override get_id to include user type"""
        return f"{self.id}:{'judge' if self.is_judge else 'participant'}"

    @staticmethod
    def get_user_from_id(user_id):
        """Get user from the combined ID string"""
        try:
            user_id, user_type = user_id.split(':')
            user = User.query.get(int(user_id))
            if user and ((user_type == 'judge' and user.is_judge) or 
                        (user_type == 'participant' and not user.is_judge)):
                return user
        except (ValueError, AttributeError):
            return None
        return None

    @property
    def can_have_team(self):
        """Check if user can have a team (only participants)"""
        return not self.is_judge

    def is_participant(self):
        """Check if user is a participant (not a judge)"""
        return not self.is_judge

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    disappearance_date = db.Column(db.DateTime)
    birth_date = db.Column(db.DateTime)
    age_at_disappearance = db.Column(db.Integer)
    current_age = db.Column(db.Integer)
    disappearance_location = db.Column(db.String(200))
    gender = db.Column(db.String(20))
    eye_color = db.Column(db.String(50))
    hair_color = db.Column(db.String(50))
    hair_type = db.Column(db.String(50))
    hair_length = db.Column(db.String(50))
    body_type = db.Column(db.String(50))
    height = db.Column(db.Float)
    weight = db.Column(db.Integer)
    last_seen_clothing = db.Column(db.String(200))
    photo_path = db.Column(db.String(255))  # Almacenar la ruta de la imagen en lugar de base64
    cndes_id = db.Column(db.String(32), unique=True)
    first_name = db.Column(db.String(100))
    last_name1 = db.Column(db.String(100))
    last_name2 = db.Column(db.String(100))
    disappearance_type = db.Column(db.String(20))
    needs = db.Column(db.Text)
    is_found = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref=db.backref('created_cases', lazy=True))
    participants = db.relationship('Participant', backref='case', lazy=True)

    def __repr__(self):
        return f'<Case {self.title}>'

    def to_dict(self):
        """Convert case to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'disappearance_date': self.disappearance_date.isoformat() if self.disappearance_date else None,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'age_at_disappearance': self.age_at_disappearance,
            'current_age': self.current_age,
            'disappearance_location': self.disappearance_location,
            'gender': self.gender,
            'eye_color': self.eye_color,
            'hair_color': self.hair_color,
            'hair_type': self.hair_type,
            'hair_length': self.hair_length,
            'body_type': self.body_type,
            'height': self.height,
            'weight': self.weight,
            'last_seen_clothing': self.last_seen_clothing,
            'photo_path': self.photo_path,
            'cndes_id': self.cndes_id,
            'first_name': self.first_name,
            'last_name1': self.last_name1,
            'last_name2': self.last_name2,
            'disappearance_type': self.disappearance_type,
            'needs': self.needs,
            'is_found': self.is_found,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by
        }

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    document_type = db.Column(db.String(50))
    document_number = db.Column(db.String(50))
    role = db.Column(db.String(100))  # e.g., 'family_member', 'witness', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Participant {self.name}>'

    def to_dict(self):
        """Convert participant to dictionary for API responses"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'name': self.name,
            'document_type': self.document_type,
            'document_number': self.document_number,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class FlagSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    flag = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    source_url = db.Column(db.String(500))
    photo_path = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_correct = db.Column(db.Boolean, nullable=True)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    review_notes = db.Column(db.Text)

    # Relationships
    case = db.relationship('Case', backref=db.backref('flag_submissions', lazy=True))
    team = db.relationship('Team', backref=db.backref('flag_submissions', lazy=True))
    reviewer = db.relationship('User', backref=db.backref('reviewed_submissions', lazy=True))

    # Constantes para las categorías y puntos
    CATEGORIES = {
        'FRIENDS': ('Amigos', 10),
        'EMPLOYMENT': ('Empleo', 15),
        'FAMILY': ('Familia', 20),
        'BASIC_INFO': ('Información básica del MP', 50),
        'ADVANCED_INFO': ('Información avanzada del MP', 100),
        'LAST_SEEN': ('Día visto por última vez', 300),
        'TIMELINE': ('Avanzar en la línea de tiempo', 700),
        'DARKWEB': ('Darkweb', 1000),
        'LOCATION': ('Ubicación', 5000)
    }

    @property
    def category_name(self):
        """Get the human-readable category name"""
        return self.CATEGORIES.get(self.category, ('Desconocida', 0))[0]

    def __repr__(self):
        return f'<FlagSubmission {self.id} for Case {self.case_id}>'

    def to_dict(self):
        """Convert submission to dictionary for API responses"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'team_id': self.team_id,
            'flag': self.flag,
            'category': self.category,
            'category_name': self.category_name,
            'points': self.points,
            'source_url': self.source_url,
            'photo_path': self.photo_path,
            'submitted_at': self.submitted_at.isoformat(),
            'is_correct': self.is_correct,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
            'notes': self.notes,
            'review_notes': self.review_notes
        }

class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 addresses can be up to 45 chars
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LoginAttempt {self.username} from {self.ip_address}>' 