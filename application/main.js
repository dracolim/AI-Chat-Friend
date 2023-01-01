function ipLookUp() {
  return new Promise((resolve, reject) => {
    $.ajax('http://ip-api.com/json')
      .then(
        function success(response) {
          resolve(response);
        },
        function fail(data, status) {
          reject(status);
        }
      );
  });
}

function chatBot() {
  this.respondTo = async function (input) {
    try {
      this.input = input.toLowerCase();
      const response = await ipLookUp();
      const lat = response.lat;
      const lon = response.lon;

      // Send an HTTP request to the Flask route
      const fetchResponse = await fetch("http://localhost:5008/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          message: input,
          lat: lat,
          lon: lon
        }),    
      });
      const data = await fetchResponse.json();

      // Return the response from the Flask route
      return data.response;
    } 
    catch (error) {
      // Handle any errors that may occur
      console.error(error);
      return "Sorry, there was an error processing your request.";
    }
  };
}

$(function () {
    var you = "You";
    var robot = "Chatbot";

    var delayStart = 400;
    var delayEnd = 800;

    var bot = new chatBot();
    var chat = $(".chat");
    var waiting = 0;
    $(".busy").text(robot + " is typing...");

    var submitChat = function () {
      var input = $(".input input").val();
      if (input == "") return;

      $(".input input").val("");
      updateChat(you, input);

      var reply = bot.respondTo(input);

      reply.then((result) => {
        reply = result
      });

      if (reply == null) return;

      var latency = Math.floor(
        Math.random() * (delayEnd - delayStart) + delayStart
      );
      $(".busy").css("display", "block");
      waiting++;
      setTimeout(function () {
        if (typeof reply === "string") {
          updateChat(robot, reply);
        } else {
          for (var r in reply) {
            updateChat(robot, reply[r]);
          }
        }
        if (--waiting == 0) $(".busy").css("display", "none");
      }, latency);
    };

    var updateChat = function (party, text) {
      var style = "you";
      if (party != you) {
        style = "other";
      }

      var line = $(
        '<div><span class="party"></span> <span class="text"></span></div>'
      );
      line
      .find(".party")
      .addClass(style)
      .text(party + ":");
      line.find(".text").html(text.replace(/\n/g, "<br>"));

      chat.append(line);

      chat.stop().animate({
        scrollTop: chat.prop("scrollHeight")
      });
    };

    $(".input").bind("keydown", function (e) {
      if (e.keyCode == 13) {
        submitChat();
      }
    });
    $(".input a").bind("click", submitChat);

    updateChat(robot, "Hello!");
});