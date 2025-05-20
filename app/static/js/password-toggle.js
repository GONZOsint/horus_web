/**
 * Password Toggle Functionality
 * Handles showing/hiding password fields
 */

function initializePasswordToggles(toggleConfigs) {
    toggleConfigs.forEach(config => {
        const button = document.querySelector(`#${config.buttonId}`);
        const input = document.querySelector(`#${config.inputId}`);
        
        if (button && input) {
            button.addEventListener('click', function() {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.querySelector('i').classList.toggle('fa-eye');
                this.querySelector('i').classList.toggle('fa-eye-slash');
            });
        }
    });
} 