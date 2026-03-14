/**
 * api.js - Fetch wrappers and token storage for E Lost & Found
 * All API calls go through this module. Token is stored in localStorage.
 */

var api = (function() {
  // API base URL - change this when deploying (e.g. https://your-domain.com/api or leave empty for same-origin)
  var BASE_URL = window.API_BASE_URL || 'http://localhost:8000';
  var TOKEN_KEY = 'elostfound_token';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  }

  function headers(includeAuth) {
    var h = { 'Content-Type': 'application/json' };
    if (includeAuth !== false) {
      var t = getToken();
      if (t) h['Authorization'] = 'Bearer ' + t;
    }
    return h;
  }

  function get(path) {
    return fetch(BASE_URL + path, { method: 'GET', headers: headers() })
      .then(function(res) {
        if (!res.ok) return res.json().then(function(j) { throw new Error(j.detail || res.statusText); });
        return res.json();
      });
  }

  function post(path, body) {
    return fetch(BASE_URL + path, {
      method: 'POST',
      headers: headers(),
      body: body ? JSON.stringify(body) : undefined,
    }).then(function(res) {
      if (!res.ok) return res.json().then(function(j) { throw new Error(j.detail || res.statusText); });
      return res.json();
    });
  }

  function patch(path, body) {
    return fetch(BASE_URL + path, {
      method: 'PATCH',
      headers: headers(),
      body: body ? JSON.stringify(body) : undefined,
    }).then(function(res) {
      if (!res.ok) return res.json().then(function(j) { throw new Error(j.detail || res.statusText); });
      return res.json();
    });
  }

  /**
   * Upload form data (multipart) - for lost/found with image.
   * formData should be FormData instance with field names matching API.
   */
  function upload(path, formData) {
    var h = {};
    var t = getToken();
    if (t) h['Authorization'] = 'Bearer ' + t;
    // Do not set Content-Type; browser sets multipart boundary
    return fetch(BASE_URL + path, {
      method: 'POST',
      headers: h,
      body: formData,
    }).then(function(res) {
      if (!res.ok) return res.json().then(function(j) { throw new Error(j.detail || res.statusText); });
      return res.json();
    });
  }

  return {
    getToken: getToken,
    setToken: setToken,
    get: get,
    post: post,
    patch: patch,
    upload: upload,
    getStats: function() { return get('/stats'); },
  };
})();
