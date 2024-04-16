window.onload = function () {
  adjustImageMargin();

  document
    .getElementById("search-bar")
    .addEventListener("keydown", function (event) {
      if (event.keyCode === 13) {
        event.preventDefault();
        addItem();
      }
    });
};

window.onresize = function () {
  adjustImageMargin();
};

var colorIdentities = [];
var cards = {};

function adjustImageMargin() {
  var container = document.getElementById("image-container");
  var images = container.getElementsByTagName("img");

  var totalImageWidth = 0;
  for (var i = 0; i < images.length; i++) {
    totalImageWidth += images[i].offsetWidth;
  }

  var availableWidth = container.offsetWidth;

  var maxMargin = 10;

  var margin = Math.min(
    (availableWidth - totalImageWidth) / (images.length - 1),
    maxMargin
  );

  for (var i = 0; i < images.length; i++) {
    images[i].style.marginRight = margin + "px";
  }
}

function addItem() {
  var card_name = document.getElementById("search-bar").value;

  var url =
    "https://api.scryfall.com/cards/named?fuzzy=" +
    encodeURIComponent(card_name);

  fetch(url)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`No card found for \"${card_name}\".`);
      }
      return response.json();
    })
    .then((data) => {
      if (!data || Object.keys(data).length === 0) {
        throw new Error(`No card found for \"${card_name}\".`);
      }

      cards[data.name] = data;

      var img = document.createElement("img");
      img.src = data["image_uris"]["png"];
      img.setAttribute("data-name", data.name);
      img.onload = adjustImageMargin;

      var link = document.createElement("a");
      link.href = data["scryfall_uri"];
      link.target = "_blank";
      link.appendChild(img);

      var closeButton = document.createElement("span");
      closeButton.textContent = "X";
      closeButton.classList.add("close-button");
      closeButton.onclick = function (event) {
        event.preventDefault();
        link.remove();
        delete cards[img.getAttribute("data-name")];
        console.log(cards);
      };
      link.appendChild(closeButton);

      document.getElementById("image-container").appendChild(link);

      document.getElementById("search-bar").value = "";
    })
    .catch((error) => {
      console.error("Error:", error);
      var errorMessageDiv = document.getElementById("error-message"); // Get the div
      errorMessageDiv.textContent = error.message; // Set the text content of the div to the error message
      errorMessageDiv.style.textAlign = "center"; // Center the text
    });
  console.log(cards);
}
