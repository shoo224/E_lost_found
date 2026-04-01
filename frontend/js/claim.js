/**
 * claim.js - Claim section: browse reports and submit claim requests.
 */
(function() {
  var msgEl = document.getElementById("msg");
  var loginStateEl = document.getElementById("login-state");
  var lostSelectEl = document.getElementById("lost-select");
  var foundSelectEl = document.getElementById("found-select");
  var lostListEl = document.getElementById("lost-items-list");
  var foundListEl = document.getElementById("found-items-list");

  function showMsg(text, type) {
    msgEl.textContent = text;
    msgEl.className = "alert alert-" + (type || "info");
    msgEl.classList.remove("hide");
  }

  function updateLoginState() {
    loginStateEl.textContent = api.getToken() ? "Logged in" : "Not logged in";
  }

  function fillSelect(selectEl, items, itemType) {
    selectEl.innerHTML = "";
    if (!items.length) {
      var emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "No " + itemType + " reports available";
      selectEl.appendChild(emptyOption);
      return;
    }
    items.forEach(function(item) {
      var opt = document.createElement("option");
      opt.value = item.id;
      opt.textContent = item.item_name + " | " + (item.status || "open") + " | " + item.id;
      selectEl.appendChild(opt);
    });
  }

  function renderList(listEl, items, itemType) {
    if (!items.length) {
      listEl.innerHTML = "<li>No " + itemType + " reports yet.</li>";
      return;
    }
    listEl.innerHTML = "";
    items.forEach(function(item) {
      var li = document.createElement("li");
      var extra = itemType === "found"
        ? ("Source: " + (item.submitted_by || "student") + ", Location: " + (item.location || "-"))
        : ("Lost at: " + (item.where_lost || "-") + ", Email: " + (item.college_email || "-"));
      li.className = "p-3 rounded-lg border border-slate-200 dark:border-slate-800";
      li.textContent = item.item_name + " | Status: " + (item.status || "open") + " | " + extra + " | ID: " + item.id;
      listEl.appendChild(li);
    });
  }

  function loadClaimableItems() {
    api.get("/claims/claimable-items").then(function(data) {
      var lostItems = data.lost_items || [];
      var foundItems = data.found_items || [];
      fillSelect(lostSelectEl, lostItems, "lost");
      fillSelect(foundSelectEl, foundItems, "found");
      renderList(lostListEl, lostItems, "lost");
      renderList(foundListEl, foundItems, "found");
    }).catch(function(err) {
      showMsg(err.message || "Failed to load claimable items.", "error");
    });
  }

  document.getElementById("claim-send-otp").onclick = function() {
    var email = document.getElementById("claim-email").value.trim();
    if (!email) {
      showMsg("Enter college email.", "error");
      return;
    }
    api.post("/auth/otp/send", { email: email }).then(function() {
      showMsg("OTP sent to your email.", "success");
    }).catch(function(err) {
      showMsg(err.message || "Failed to send OTP.", "error");
    });
  };

  document.getElementById("claim-verify-otp").onclick = function() {
    var email = document.getElementById("claim-email").value.trim();
    var otp = document.getElementById("claim-otp").value.trim();
    if (!email || !otp) {
      showMsg("Enter email and OTP.", "error");
      return;
    }
    api.post("/auth/otp/verify", { email: email, otp: otp }).then(function(data) {
      api.setToken(data.access_token);
      updateLoginState();
      showMsg("Logged in successfully.", "success");
    }).catch(function(err) {
      showMsg(err.message || "Invalid OTP.", "error");
    });
  };

  document.getElementById("btn-submit-claim").onclick = function() {
    if (!api.getToken()) {
      showMsg("Please log in first.", "error");
      return;
    }
    var lostId = lostSelectEl.value;
    var foundId = foundSelectEl.value;
    if (!lostId || !foundId) {
      showMsg("Select both lost and found reports.", "error");
      return;
    }
    api.post("/claims", { found_item_id: foundId, lost_item_id: lostId }).then(function() {
      showMsg("Claim request submitted. Admin will review.", "success");
      loadClaimableItems();
    }).catch(function(err) {
      showMsg(err.message || "Failed to submit claim.", "error");
    });
  };

  updateLoginState();
  loadClaimableItems();
})();
