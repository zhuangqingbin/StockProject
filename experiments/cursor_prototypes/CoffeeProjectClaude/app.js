/**
 * Artisan Espresso Club - Login Page Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const form = document.getElementById('loginForm');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const togglePasswordBtn = document.getElementById('togglePassword');
  const sixMonthToggle = document.getElementById('sixMonthToggle');
  const submitBtn = document.getElementById('submitBtn');
  const submitSubtext = document.getElementById('submitSubtext');
  const toast = document.getElementById('toast');
  const toastTitle = document.getElementById('toastTitle');
  const toastMessage = document.getElementById('toastMessage');

  // Password visibility toggle
  togglePasswordBtn.addEventListener('click', () => {
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    togglePasswordBtn.classList.toggle('active', isPassword);
    togglePasswordBtn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
  });

  // Update submit button text based on 6-month toggle
  const updateSubmitText = () => {
    if (sixMonthToggle.checked) {
      submitSubtext.textContent = 'Continue your 6-month membership';
    } else {
      submitSubtext.textContent = 'Continue with monthly billing';
    }
  };

  sixMonthToggle.addEventListener('change', updateSubmitText);
  updateSubmitText();

  // Show toast notification
  const showToast = (title, message, duration = 4000) => {
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    toast.hidden = false;

    setTimeout(() => {
      toast.hidden = true;
    }, duration);
  };

  // Form validation
  const validateEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  // Form submission
  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // Validate email
    if (!email) {
      showToast('Email required', 'Please enter your email address.');
      emailInput.focus();
      return;
    }

    if (!validateEmail(email)) {
      showToast('Invalid email', 'Please enter a valid email address.');
      emailInput.focus();
      return;
    }

    // Validate password
    if (!password) {
      showToast('Password required', 'Please enter your password.');
      passwordInput.focus();
      return;
    }

    if (password.length < 8) {
      showToast('Password too short', 'Password must be at least 8 characters.');
      passwordInput.focus();
      return;
    }

    // Simulate successful login
    const planType = sixMonthToggle.checked ? '6-month' : 'monthly';
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.style.opacity = '0.7';
    submitBtn.querySelector('.submit__text').textContent = 'Signing in...';

    // Simulate API call
    setTimeout(() => {
      showToast(
        'Welcome back!',
        `Redirecting to your ${planType} member dashboard...`,
        5000
      );

      // Re-enable button after toast
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.querySelector('.submit__text').textContent = 'Sign in to your account';
      }, 2000);
    }, 1500);
  });

  // Input focus effects
  const inputs = document.querySelectorAll('.field__input');
  inputs.forEach(input => {
    input.addEventListener('focus', () => {
      input.closest('.field')?.classList.add('field--focused');
    });

    input.addEventListener('blur', () => {
      input.closest('.field')?.classList.remove('field--focused');
    });
  });

  // OAuth button interactions (demo)
  const oauthButtons = document.querySelectorAll('.oauth__btn');
  oauthButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const provider = btn.classList.contains('oauth__btn--google') ? 'Google' : 'Apple';
      showToast(
        `${provider} Sign-in`,
        `Redirecting to ${provider} authentication...`
      );
    });
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });

  // Keyboard accessibility
  document.addEventListener('keydown', (e) => {
    // Close toast on Escape
    if (e.key === 'Escape' && !toast.hidden) {
      toast.hidden = true;
    }
  });
});
