/**
 * admin.js - Admin login (OTP via /auth/otp/send and /auth/otp/verify), add found item, approve/reject claims
 * Admin login uses auth router; then we use token for /found/admin and /claims
 */

(function() {
  var baseUrl = window.API_BASE_URL || 'http://localhost:8000';
  var msgEl = document.getElementById('msg');
  var loginDiv = document.getElementById('admin-login');
  var panelDiv = document.getElementById('admin-panel');

  function showMsg(text, type) {
    if (!msgEl) return;
    msgEl.textContent = text;
    msgEl.className = 'alert alert-' + (type || 'info');
    msgEl.classList.remove('hide');
  }

  function hideMsg() {
    if (!msgEl) return;
    msgEl.classList.add('hide');
  }

  function checkAdminLoggedIn() {
    // If there is no login block (admin-panel.html), do nothing and keep panel visible
    if (!loginDiv && panelDiv) {
      return;
    }
    // On admin.html, keep login visible by default
    if (loginDiv && panelDiv) {
      loginDiv.classList.remove('hide');
      panelDiv.classList.add('hide');
    }
  }

  // Admin login now uses email + password (no OTP) for admin panel (on admin.html)
  var sendOtpBtn = document.getElementById('btn-send-otp');
  if (sendOtpBtn) {
    sendOtpBtn.onclick = function() {
      showMsg('Admin login uses email + password only. Enter your admin email and password, then click Login.', 'info');
    };
  }

  var loginBtn = document.getElementById('btn-verify-otp');
  if (loginBtn) {
    loginBtn.onclick = function() {
      var emailInput = document.getElementById('admin-email');
      var passwordInput = document.getElementById('admin-otp');
      if (!emailInput || !passwordInput) return;
      var email = emailInput.value.trim();
      var password = passwordInput.value.trim();
      if (!email || !password) { showMsg('Enter email and password.', 'error'); return; }
      hideMsg();
      api.post('/admin/login-password', { email: email, password: password }).then(function(data) {
        if (data.user && data.user.role === 'admin') {
          api.setToken(data.access_token);
          var display = document.getElementById('admin-email-display');
          if (display) display.textContent = data.user.email || email;
          if (loginDiv && panelDiv) {
            loginDiv.classList.add('hide');
            panelDiv.classList.remove('hide');
          }
          loadClaims();
          showMsg('Logged in.', 'success');
        } else {
          showMsg('This email is not an admin.', 'error');
        }
      }).catch(function(e) {
        showMsg(e.message || 'Invalid credentials or not admin.', 'error');
      });
    };
  }

  // Direct button: no credentials, go to separate admin panel page
  var directBtn = document.getElementById('btn-direct');
  if (directBtn) {
    directBtn.onclick = function() {
      window.location.href = 'admin-panel.html';
    };
  }

  var logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.onclick = function() {
      api.setToken(null);
      if (loginDiv && panelDiv) {
        loginDiv.classList.remove('hide');
        panelDiv.classList.add('hide');
      }
      var emailInput = document.getElementById('admin-email');
      var passwordInput = document.getElementById('admin-otp');
      if (emailInput) emailInput.value = '';
      if (passwordInput) passwordInput.value = '';
      showMsg('Logged out.', 'success');
    };
  }

  // Add found item (admin)
  document.getElementById('form-admin-found').onsubmit = function(e) {
    e.preventDefault();
    var formData = new FormData();
    formData.append('item_name', document.getElementById('admin-item_name').value);
    formData.append('date_found', document.getElementById('admin-date_found').value);
    formData.append('time_found', document.getElementById('admin-time_found').value || '');
    formData.append('description', document.getElementById('admin-description').value);
    formData.append('location', document.getElementById('admin-location').value);
    var img = document.getElementById('admin-image').files[0];
    if (img) formData.append('image', img);

    api.upload('/found/admin', formData).then(function(data) {
      showMsg('Found item added. ID: ' + data.id, 'success');
      document.getElementById('form-admin-found').reset();
    }).catch(function(err) {
      showMsg(err.message || 'Failed to add.', 'error');
    });
  };

  function loadClaims() {
    var listEl = document.getElementById('claims-list');
    listEl.innerHTML = '<li>Loading...</li>';
    api.get('/claims').then(function(data) {
      var claims = data.claims || [];
      if (claims.length === 0) {
        listEl.innerHTML = '<li>No claims to review.</li>';
        return;
      }
      listEl.innerHTML = '';
      claims.forEach(function(c) {
        var li = document.createElement('li');
        var found = c.found_item || {};
        var lost = c.lost_item || {};
        var title = '<strong>Claim #' + c.id + '</strong> <span class="meta">(' + (c.status || 'pending') + ')</span>';
        var details = '<div class="meta">Found: ' + (found.item_name || c.found_item_id) + ' | Source: ' + (found.submitted_by || '-') + '</div>' +
          '<div class="meta">Lost: ' + (lost.item_name || c.lost_item_id) + ' | Lost at: ' + (lost.where_lost || '-') + '</div>' +
          '<div class="meta">Claimed by user: ' + (c.claimed_by || '-') + '</div>';
        var actions = '';
        if (c.status === 'pending') {
          actions = '<div class="claim-actions">' +
            '<button type="button" class="btn btn-success approve-claim" data-id="' + c.id + '">Approve</button>' +
            '<button type="button" class="btn btn-danger reject-claim" data-id="' + c.id + '">Reject</button>' +
            '</div>';
        }
        li.innerHTML = title + details + actions;
        listEl.appendChild(li);
      });
      listEl.querySelectorAll('.approve-claim').forEach(function(btn) {
        btn.onclick = function() { updateClaim(btn.getAttribute('data-id'), 'approved'); };
      });
      listEl.querySelectorAll('.reject-claim').forEach(function(btn) {
        btn.onclick = function() { updateClaim(btn.getAttribute('data-id'), 'rejected'); };
      });
      if (listEl.innerHTML === '') listEl.innerHTML = '<li>No claims available.</li>';
    }).catch(function() {
      // If we are on admin-panel.html and token isn't admin, try direct login and retry once.
      if (!loginDiv && panelDiv) {
        api.post('/admin/direct-login', {}).then(function(d) {
          if (d && d.access_token) {
            api.setToken(d.access_token);
            loadClaims();
            return;
          }
          listEl.innerHTML = '<li>Failed to load claims.</li>';
        }).catch(function() {
          listEl.innerHTML = '<li>Failed to load claims.</li>';
        });
      } else {
        listEl.innerHTML = '<li>Failed to load claims.</li>';
      }
    });
  }

  function updateClaim(claimId, status) {
    api.patch('/claims/' + claimId, { status: status }).then(function() {
      showMsg('Claim ' + status + '.', 'success');
      loadClaims();
    }).catch(function(e) {
      showMsg(e.message || 'Failed.', 'error');
    });
  }

  checkAdminLoggedIn();

  // admin-panel.html has no login form: always run dev direct login first.
  // This avoids 403s caused by a stale/non-admin token in localStorage.
  if (!loginDiv && panelDiv && document.getElementById('claims-list')) {
    api.post('/admin/direct-login', {}).then(function(data) {
      if (data && data.access_token) {
        api.setToken(data.access_token);
        var display = document.getElementById('admin-email-display');
        if (display) {
          display.textContent = (data.user && data.user.email) ? data.user.email : 'Direct admin (dev)';
        }
      }
      loadClaims();
    }).catch(function() {
      // If direct login fails, fall back to whatever token exists.
      if (api.getToken && api.getToken()) loadClaims();
    });
    return;
  }

  // admin.html: if token exists already, load claims.
  if (api.getToken && api.getToken() && document.getElementById('claims-list')) {
    loadClaims();
  }
})();
