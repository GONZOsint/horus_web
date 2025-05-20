from app import create_app, db
from app.models import User

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if test user exists
        if not User.query.filter_by(username='test').first():
            # Create test user
            user = User(username='test', is_judge=False)
            user.set_password('test123')
            db.session.add(user)
            
            # Create test judge
            judge = User(username='judge', is_judge=True)
            judge.set_password('judge123')
            db.session.add(judge)
            
            # Commit changes
            db.session.commit()
            print("Test users created successfully!")
        else:
            print("Test users already exist!")

if __name__ == '__main__':
    init_db() 