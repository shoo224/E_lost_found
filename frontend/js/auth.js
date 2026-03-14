/**
 * auth.js - Login via OTP and token storage
 * Step 1: requestOtp(email) -> OTP sent to email
 * Step 2: verifyOtp(email, otp) -> returns token + user, save token
 */

// Shared helpers for admin login (admin.html uses auth + admin.js)
function showMsg(elId, text, type) {
  var el = document.getElementById(elId);
  if (!el) return;
  el.textContent = text;
  el.className = 'alert alert-' + (type || 'info');
  el.classList.remove('hide');
}

function hideMsg(elId) {
  var el = document.getElementById(elId);
  if (el) el.classList.add('hide');
}

// Admin login: send OTP to admin email (uses /auth/otp/send)
// Verify OTP with /auth/otp/verify -> get JWT, store token, show admin panel
// Implemented in admin.js for admin-specific flow
