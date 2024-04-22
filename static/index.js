window.onload = function () {
  adjustImageMargin();

  document
    .getElementById("search-bar")
    .addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        addItem();
      }
    });
};

window.onresize = adjustImageMargin;

window.addEventListener("DOMContentLoaded", function () {
  document.getElementById("submit").addEventListener("click", function () {
    var imageContainer = document.getElementById("image-container");
    imageContainer.style.maxWidth = "40vw";
    imageContainer.style.marginRight = "auto";
    imageContainer.style.marginLeft = "0";
    adjustImageMargin();
  });
});

var cards = {};

document.getElementById("submit").addEventListener("click", function (event) {
  event.preventDefault();

  fetch("/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(cards),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      sortedCommanders = Object.entries(data)
        .sort((a, b) => b[1].score - a[1].score)
        .slice(0, 10)
        .map(([commander, data]) => ({ commander, data }));

      console.log(sortedCommanders);
      displayCommanders(sortedCommanders);
    })
    .catch((error) => {
      console.error("Error:", error);
    });
});

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

      var container = document.createElement("div");
      container.classList.add("container");

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
        container.remove();
        delete cards[img.getAttribute("data-name")];
        adjustImageMargin();
        console.log(cards);
      };

      container.appendChild(link);
      container.appendChild(closeButton);

      document.getElementById("image-container").appendChild(container);

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

function displayCommanders(top_10_commanders) {
  const container = document.getElementById("right-side-container");
  container.innerHTML = "";
  container.style.overflowY = "scroll";

  top_10_commanders.forEach((commanderData) => {
    const imgContainer = document.createElement("div");

    if (commanderData.data.data.card_faces) {
      const doubleContainer = document.createElement("div");
      doubleContainer.style.position = "relative";
      doubleContainer.style.maxWidth = "90%";
      doubleContainer.style.left = "0";

      const sizeHolder = document.createElement("img");
      sizeHolder.src = commanderData.data.data.card_faces[0].image_uris.png;
      sizeHolder.style.opacity = "0";
      doubleContainer.appendChild(sizeHolder);

      const img1 = document.createElement("img");
      img1.src = commanderData.data.data.card_faces[0].image_uris.png;
      img1.style.position = "absolute";
      img1.style.left = "0";
      img1.style.bottom = "0";
      img1.style.zIndex = "3";
      doubleContainer.appendChild(img1);

      const img2 = document.createElement("img");
      img2.src = commanderData.data.data.card_faces[1].image_uris.png;
      img2.style.position = "absolute";
      img2.style.right = "0";
      img2.style.top = "0";
      img2.style.zIndex = "2";
      img2.onmouseover = function () {
        this.style.zIndex = "4";
      };
      img2.onmouseout = function () {
        this.style.zIndex = "2";
      };
      doubleContainer.appendChild(img2);

      imgContainer.appendChild(doubleContainer);
    } else if (commanderData.commander.includes("+")) {
      const partnerContainer = document.createElement("div");
      partnerContainer.style.position = "relative";
      partnerContainer.style.maxWidth = "90%";
      partnerContainer.style.left = "0";

      const partnerSizeHolder = document.createElement("img");
      partnerSizeHolder.src = commanderData.data.data[0].image_uris.png;
      partnerSizeHolder.style.opacity = "0";
      partnerContainer.appendChild(partnerSizeHolder);

      const img1 = document.createElement("img");
      img1.src = commanderData.data.data[0].image_uris.png;
      img1.style.position = "absolute";
      img1.style.left = "0";
      img1.style.bottom = "0";
      img1.style.zIndex = "3";
      partnerContainer.appendChild(img1);

      const img2 = document.createElement("img");
      img2.src = commanderData.data.data[1].image_uris.png;
      img2.style.position = "absolute";
      img2.style.right = "0";
      img2.style.top = "0";
      img2.style.zIndex = "2";
      img2.onmouseover = function () {
        this.style.zIndex = "4";
      };
      img2.onmouseout = function () {
        this.style.zIndex = "2";
      };
      partnerContainer.appendChild(img2);

      imgContainer.appendChild(partnerContainer);
    } else {
      const singleContainer = document.createElement("div");
      const img = document.createElement("img");
      img.src = commanderData.data.data.image_uris.png;
      singleContainer.appendChild(img);
      imgContainer.appendChild(singleContainer);
    }

    const scoreDiv = document.createElement("div");
    scoreDiv.textContent = `Score: ${commanderData.data.score}/10`;
    imgContainer.appendChild(scoreDiv);

    container.appendChild(imgContainer);
  });
}

function printCommanders() {
  console.log(top_10_commanders);
}
