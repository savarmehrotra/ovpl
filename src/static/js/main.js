window.ADS = window.ADS || {};
(function(ADS) {
  var Persona = function(logged_in_user, login_url, logout_url) {
    navigator.id.watch({
      loggedInUser: logged_in_user,
      //when an user logs in
      onlogin: function(assertion) {
        //verify assertion and login the user
        $.ajax({
          type: 'POST',
          url: login_url,
          data: {assertion: assertion},
          success: function(data) {
            if(data['status'] == 'okay') {
              console.log('successful login..', data);
              window.location.href = 'http://' + window.location.host + '/';
            }
            else if(data['status'] == 'error') {
              console.log('not authorized..', data);
              $('#notif').html(data['msg']);
              $('#notif').show();
            }
          },
          error: function() {
            navigator.id.logout();
          }
        });
      },
      onlogout: function() {
        $.ajax({
          type: 'POST',
          url: logout_url,
          success: function() {
            window.location.href = window.location.origin;
          },
          error: function() {
          }
        });
      }
    });

    return this;
  }

  Persona.prototype.attachLogin = function(login_btn) {
    // check if the login button exists
    if($(login_btn).length) {
      $(login_btn).click(function(e) {
        e.preventDefault();
        navigator.id.request();
      });
    }
  };

  Persona.prototype.attachLogout = function(logout_btn) {
    // check if the logout button exists
    if($(logout_btn).length) {
      $(logout_btn).click(function(e) {
        e.preventDefault();
        navigator.id.logout();
      });
    }
  };

  var init = function() {
    this.persona = new Persona(ADS.loggedInUser(), ADS.loginURL(), ADS.logoutURL());
    //console.log(persona);
    var login_btn = $('#login')[0];
    var logout_btn = $('#logout')[0];
    //console.log(login_btn);
    this.persona.attachLogin(login_btn);
    this.persona.attachLogout(logout_btn);
  };

  window.onload = function() {
    init();
  };
})(window.ADS);
