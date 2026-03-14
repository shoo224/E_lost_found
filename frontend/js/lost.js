/**
 * lost.js - Item Lost form: OTP verify college email, then submit form
 * Step 1: Send OTP to college email (POST /lost/otp/send)
 * Step 2: Verify OTP (POST /lost/otp/verify)
 * Step 3: Submit form (POST /lost with multipart)
 */

(function() {
  var msgEl = document.getElementById('msg');
  var emailVerified = false;

  function showMsg(text, type) {
    msgEl.textContent = text;
    msgEl.className = 'alert alert-' + (type || 'info');
    msgEl.classList.remove('hide');
  }

  function hideMsg() {
    msgEl.classList.add('hide');
  }

  var baseUrl = window.API_BASE_URL || 'http://localhost:8000';

  // Send OTP for college email
  document.getElementById('btn-send-otp').onclick = function() {
    var email = document.getElementById('college_email').value.trim();
    if (!email) { showMsg('Enter college email.', 'error'); return; }
    hideMsg();
    fetch(baseUrl + '/lost/otp/send?email=' + encodeURIComponent(email), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(function(r) { return r.json().then(function(j) { if (!r.ok) throw new Error(j.detail || r.statusText); return j; }); })
      .then(function() { showMsg('OTP sent to your email.', 'success'); })
      .catch(function(e) { showMsg(e.message || 'Failed to send OTP.', 'error'); });
  };

  // Verify OTP
  document.getElementById('btn-verify-otp').onclick = function() {
    var email = document.getElementById('college_email').value.trim();
    var otp = document.getElementById('otp').value.trim();
    if (!email || !otp) { showMsg('Enter email and OTP.', 'error'); return; }
    hideMsg();
    fetch(baseUrl + '/lost/otp/verify?email=' + encodeURIComponent(email) + '&otp=' + encodeURIComponent(otp), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(function(r) { return r.json().then(function(j) { if (!r.ok) throw new Error(j.detail || r.statusText); return j; }); })
      .then(function() {
        emailVerified = true;
        document.getElementById('college_email_form').value = email;
        document.getElementById('email-verified').classList.remove('hide');
        showMsg('Email verified. You can submit the form below.', 'success');
      })
      .catch(function(e) { showMsg(e.message || 'Invalid OTP.', 'error'); });
  };

  // Submit lost item form (multipart)
  document.getElementById('form-lost').onsubmit = function(e) {
    e.preventDefault();
    if (!emailVerified) {
      showMsg('Please verify your college email with OTP first.', 'error');
      return;
    }
    var form = e.target;
    var formData = new FormData();
    formData.append('name', document.getElementById('name').value);
    formData.append('college_email', document.getElementById('college_email_form').value);
    formData.append('where_lost', document.getElementById('where_lost').value);
    formData.append('when_lost', document.getElementById('when_lost').value);
    formData.append('item_name', document.getElementById('item_name').value);
    formData.append('description', document.getElementById('description').value);
    var img = document.getElementById('image').files[0];
    if (img) formData.append('image', img);

    document.getElementById('btn-submit').disabled = true;
    api.upload('/lost', formData)
      .then(function(data) {
        showMsg('Lost item reported. ID: ' + data.id + (data.matched_found_ids && data.matched_found_ids.length ? '. Possible matches found – check your email.' : ''), 'success');
        form.reset();
        document.getElementById('email-verified').classList.add('hide');
        emailVerified = false;
      })
      .catch(function(err) { showMsg(err.message || 'Failed to submit.', 'error'); })
      .finally(function() { document.getElementById('btn-submit').disabled = false; });
  };
})();
