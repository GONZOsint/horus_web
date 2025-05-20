/**
 * Password Strength Meter
 * Calculates and displays password strength
 */

function initializePasswordStrengthMeter(passwordInputId, meterContainerId) {
    const passwordInput = document.querySelector(`#${passwordInputId}`);
    const meterContainer = document.querySelector(`#${meterContainerId}`);
    
    if (!passwordInput || !meterContainer) return;

    const strengthMeter = meterContainer.querySelector('.progress-bar');
    const strengthText = meterContainer.querySelector('.password-strength-text');

    passwordInput.addEventListener('input', function() {
        const password = this.value;
        let strength = 0;
        let feedback = '';

        // Length check
        if (password.length >= 8) strength += 25;
        
        // Character type checks
        if (password.match(/[a-z]/)) strength += 25;
        if (password.match(/[A-Z]/)) strength += 25;
        if (password.match(/[0-9]/)) strength += 25;
        if (password.match(/[^a-zA-Z0-9]/)) strength += 25;

        // Update meter
        strengthMeter.style.width = strength + '%';

        // Set color and feedback based on strength
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