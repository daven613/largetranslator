// Large Translator Frontend - Authentication Logic

document.addEventListener('DOMContentLoaded', () => {
    // Redirect if already authenticated
    Navigation.redirectIfAuthenticated();

    // Get DOM elements
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const toggleSignup = document.getElementById('toggleSignup');
    const toggleLogin = document.getElementById('toggleLogin');
    const backToLogin = document.getElementById('backToLogin');
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');

    // Toggle between login and signup forms
    toggleSignup.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
        backToLogin.style.display = 'block';
        toggleSignup.parentElement.style.display = 'none';
    });

    toggleLogin.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        backToLogin.style.display = 'none';
        toggleSignup.parentElement.style.display = 'block';
    });

    // Handle login form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        if (!email || !password) {
            UI.showError('Please fill in all fields');
            return;
        }

        UI.setLoading(loginBtn, true);

        try {
            const response = await API.login(email, password);
            
            // Store authentication data
            Auth.setToken(response.token.access_token);
            Auth.setUserInfo(response.user);
            
            UI.showSuccess('Login successful! Redirecting...');
            
            // Redirect to upload page after a short delay
            setTimeout(() => {
                window.location.href = 'upload.html';
            }, 1000);

        } catch (error) {
            UI.showError(error.message || 'Login failed. Please check your credentials.');
        } finally {
            UI.setLoading(loginBtn, false);
        }
    });

    // Handle signup form submission
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('signupEmail').value;
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        // Validation
        if (!email || !password || !confirmPassword) {
            UI.showError('Please fill in all fields');
            return;
        }

        if (password !== confirmPassword) {
            UI.showError('Passwords do not match');
            return;
        }

        if (password.length < 6) {
            UI.showError('Password must be at least 6 characters long');
            return;
        }

        UI.setLoading(signupBtn, true);

        try {
            const response = await API.signup(email, password);
            
            // Store authentication data
            Auth.setToken(response.token.access_token);
            Auth.setUserInfo(response.user);
            
            UI.showSuccess('Account created successfully! Redirecting...');
            
            // Redirect to upload page after a short delay
            setTimeout(() => {
                window.location.href = 'upload.html';
            }, 1000);

        } catch (error) {
            UI.showError(error.message || 'Signup failed. Please try again.');
        } finally {
            UI.setLoading(signupBtn, false);
        }
    });

    // Auto-focus email field
    document.getElementById('email').focus();
}); 