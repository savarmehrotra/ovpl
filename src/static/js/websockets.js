(function() {
  var init_sockets = function() {
    var ws = new WebSocket("ws://localhost:8080/echo");

    ws.onopen = function() {
      console.log("Websockets connected");
    };

    ws.onmessage = function(evt) {
      console.log(evt.data);
      $('#logs').append(JSON.parse(evt.data)['msg'] + "<br>");
    };
  };

  $(document).ready(function() {
    init_sockets();
  });
})();

