// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle alerts
    const alertsContainer = document.querySelector('.alerts-container');
    if (alertsContainer) {
        const alerts = alertsContainer.querySelectorAll('.alert');
        const shownMessages = new Set();

        alerts.forEach(alert => {
            const message = alert.getAttribute('data-message');
            
            // Remove duplicate alerts
            if (shownMessages.has(message)) {
                alert.remove();
                return;
            }
            
            shownMessages.add(message);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
                shownMessages.delete(message);
            }, 5000);
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Password strength meter
    const passwordInput = document.querySelector('#password');
    if (passwordInput) {
        const strengthMeter = document.querySelector('.password-strength .progress-bar');
        const strengthText = document.querySelector('.password-strength-text');

        if (strengthMeter && strengthText) {
            passwordInput.addEventListener('input', function() {
                const password = this.value;
                let strength = 0;
                let feedback = '';

                // Length check
                if (password.length >= 8) strength += 25;
                // Lowercase check
                if (password.match(/[a-z]/)) strength += 25;
                // Uppercase check
                if (password.match(/[A-Z]/)) strength += 25;
                // Number check
                if (password.match(/[0-9]/)) strength += 25;

                strengthMeter.style.width = strength + '%';

                if (strength <= 25) {
                    strengthMeter.className = 'progress-bar bg-danger';
                    feedback = 'Too weak';
                } else if (strength <= 50) {
                    strengthMeter.className = 'progress-bar bg-warning';
                    feedback = 'Weak';
                } else if (strength <= 75) {
                    strengthMeter.className = 'progress-bar bg-info';
                    feedback = 'Good';
                } else {
                    strengthMeter.className = 'progress-bar bg-success';
                    feedback = 'Strong';
                }

                strengthText.textContent = 'Password strength: ' + feedback;
            });
        }
    }

    // Password visibility toggle
    const togglePasswordButtons = document.querySelectorAll('[id^="toggle"]');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const inputId = this.id.replace('toggle', '').toLowerCase();
            const input = document.getElementById(inputId);
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.querySelector('i').classList.toggle('bi-eye');
            this.querySelector('i').classList.toggle('bi-eye-slash');
        });
    });

    // Remember me functionality
    const rememberCheckbox = document.querySelector('#remember');
    if (rememberCheckbox) {
        const savedRemember = localStorage.getItem('rememberMe');
        if (savedRemember === 'true') {
            rememberCheckbox.checked = true;
        }

        rememberCheckbox.addEventListener('change', function() {
            localStorage.setItem('rememberMe', this.checked);
        });
    }

    // Modal form handling
    const modalForms = document.querySelectorAll('.modal form');
    modalForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });

    // Add smooth scrolling to all links with valid href
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        const href = anchor.getAttribute('href');
        if (href && href !== '#') {  // Only add event listener if href is not empty
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        }
    });

    // Add active class to current nav item
    const currentLocation = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
}); 