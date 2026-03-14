/**
 * found.js - Student Found form: OTP verify email, then submit form
 * Step 1: Send OTP (POST /found/student/otp/send)
 * Step 2: Verify OTP (POST /found/student/otp/verify)
 * Step 3: Submit form (POST /found/student with multipart)
 */

(function() {
  var msgEl = document.getElementById('msg');
  var verified = false;

  function showMsg(text, type) {
    msgEl.textContent = text;
    msgEl.className = 'alert alert-' + (type || 'info');
    msgEl.classList.remove('hide');
  }

  function hideMsg() {
    msgEl.classList.add('hide');
  }

  var baseUrl = window.API_BASE_URL || 'http://localhost:8000';

  document.getElementById('btn-send-otp').onclick = function() {
    var email = document.getElementById('email').value.trim();
    if (!email) { showMsg('Enter email to receive OTP.', 'error'); return; }
    hideMsg();
    fetch(baseUrl + '/found/student/otp/send?email=' + encodeURIComponent(email), { method: 'POST' })
      .then(function(r) { return r.json().then(function(j) { if (!r.ok) throw new Error(j.detail || r.statusText); return j; }); })
      .then(function() { showMsg('OTP sent to your email.', 'success'); })
      .catch(function(e) { showMsg(e.message || 'Failed to send OTP.', 'error'); });
  };

  document.getElementById('btn-verify-otp').onclick = function() {
    var email = document.getElementById('email').value.trim();
    var otp = document.getElementById('otp').value.trim();
    if (!email || !otp) { showMsg('Enter email and OTP.', 'error'); return; }
    hideMsg();
    fetch(baseUrl + '/found/student/otp/verify?email=' + encodeURIComponent(email) + '&otp=' + encodeURIComponent(otp), { method: 'POST' })
      .then(function(r) { return r.json().then(function(j) { if (!r.ok) throw new Error(j.detail || r.statusText); return j; }); })
      .then(function() {
        verified = true;
        document.getElementById('verified-msg').classList.remove('hide');
        showMsg('Verified. You can submit the form below.', 'success');
      })
      .catch(function(e) { showMsg(e.message || 'Invalid OTP.', 'error'); });
  };

  document.getElementById('form-found').onsubmit = function(e) {
    e.preventDefault();
    if (!verified) {
      showMsg('Please verify your email with OTP first.', 'error');
      return;
    }
    var formData = new FormData();
    formData.append('enrollment_number', document.getElementById('enrollment_number').value.trim());
    formData.append('email', document.getElementById('email').value.trim());
    formData.append('item_name', document.getElementById('item_name').value);
    formData.append('date_found', document.getElementById('date_found').value);
    formData.append('time_found', document.getElementById('time_found').value || '');
    formData.append('description', document.getElementById('description').value);
    formData.append('location', document.getElementById('location').value);
    var img = document.getElementById('image').files[0];
    if (img) formData.append('image', img);

    document.getElementById('btn-submit').disabled = true;
    api.upload('/found/student', formData)
      .then(function(data) {
        showMsg('Found item reported. ID: ' + data.id + (data.matched_lost_ids && data.matched_lost_ids.length ? '. Possible matches – lost persons will be emailed.' : ''), 'success');
        document.getElementById('form-found').reset();
        document.getElementById('verified-msg').classList.add('hide');
        verified = false;
      })
      .catch(function(err) { showMsg(err.message || 'Failed to submit.', 'error'); })
      .finally(function() { document.getElementById('btn-submit').disabled = false; });
  };
})();
