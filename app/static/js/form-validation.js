/**
 * Form Validation
 * Handles form validation and password confirmation
 */

function initializeFormValidation(formSelector) {
    const form = document.querySelector(formSelector);
    if (!form) return;

    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });
}

function initializePasswordConfirmation(passwordInputId, confirmInputId) {
    const passwordInput = document.querySelector(`#${passwordInputId}`);
    const confirmInput = document.querySelector(`#${confirmInputId}`);
    
    if (!passwordInput || !confirmInput) return;

    confirmInput.addEventListener('input', function() {
        if (this.value !== passwordInput.value) {
            this.setCustomValidity('Passwords do not match');
        } else {
            this.setCustomValidity('');
        }
    });

    // Also validate when password changes
    passwordInput.addEventListener('input', function() {
        if (confirmInput.value) {
            if (this.value !== confirmInput.value) {
                confirmInput.setCustomValidity('Passwords do not match');
            } else {
                confirmInput.setCustomValidity('');
            }
        }
    });
} 