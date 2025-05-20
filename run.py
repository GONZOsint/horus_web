from app import create_app, db

app = create_app()

# Increase maximum content length to 16MB to handle large base64 images
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB in bytes

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 