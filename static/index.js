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
    var rightContainer = document.getElementById("right-side-container");
    rightContainer.style.display = "flex";
    rightContainer.style.justifyContent = "center";
    rightContainer.style.alignItems = "center";
    rightContainer.innerHTML =
      '<img src="../static/images/search-spinner.gif" alt="Loading..." style="width:100px; height: 100px;">';

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

function createImageContainer(commanderData) {
  const imgContainer = document.createElement("div");

  if (commanderData.data.data.card_faces) {
    imgContainer.appendChild(createDoubleContainer(commanderData));
  } else if (commanderData.commander.includes("+")) {
    imgContainer.appendChild(createPartnerContainer(commanderData));
  } else {
    imgContainer.appendChild(createSingleContainer(commanderData));
  }

  const scoreDiv = document.createElement("div");
  scoreDiv.textContent = `Score: ${commanderData.data.score}/10`;
  imgContainer.appendChild(scoreDiv);

  return imgContainer;
}

function createDoubleContainer(commanderData) {
  const doubleContainer = document.createElement("div");
  doubleContainer.style.position = "relative";
  doubleContainer.style.maxWidth = "90%";
  doubleContainer.style.left = "0";

  const sizeHolder = createImage(
    commanderData.data.data.card_faces[0].image_uris.png,
    { opacity: "0" }
  );
  doubleContainer.appendChild(sizeHolder);

  const img1 = createImage(
    commanderData.data.data.card_faces[0].image_uris.png,
    { position: "absolute", left: "0", bottom: "0", zIndex: "3" }
  );
  doubleContainer.appendChild(img1);

  const img2 = createImage(
    commanderData.data.data.card_faces[1].image_uris.png,
    { position: "absolute", right: "0", top: "0", zIndex: "2" }
  );
  img2.onmouseover = function () {
    this.style.zIndex = "4";
  };
  img2.onmouseout = function () {
    this.style.zIndex = "2";
  };
  doubleContainer.appendChild(img2);

  return doubleContainer;
}

function createPartnerContainer(commanderData) {
  const partnerContainer = document.createElement("div");
  partnerContainer.style.position = "relative";
  partnerContainer.style.maxWidth = "90%";
  partnerContainer.style.left = "0";

  const partnerSizeHolder = createImage(
    commanderData.data.data[0].image_uris.png,
    { opacity: "0" }
  );
  partnerContainer.appendChild(partnerSizeHolder);

  const img1 = createImage(commanderData.data.data[0].image_uris.png, {
    position: "absolute",
    left: "0",
    bottom: "0",
    zIndex: "3",
  });
  partnerContainer.appendChild(img1);

  const img2 = createImage(commanderData.data.data[1].image_uris.png, {
    position: "absolute",
    right: "0",
    top: "0",
    zIndex: "2",
  });
  img2.onmouseover = function () {
    this.style.zIndex = "4";
  };
  img2.onmouseout = function () {
    this.style.zIndex = "2";
  };
  partnerContainer.appendChild(img2);

  return partnerContainer;
}

function createSingleContainer(commanderData) {
  const singleContainer = document.createElement("div");
  const img = createImage(commanderData.data.data.image_uris.png);
  singleContainer.appendChild(img);
  return singleContainer;
}

function createImage(src, styles = {}) {
  const img = document.createElement("img");
  img.src = src;
  Object.assign(img.style, styles);
  return img;
}

function displayCommanders(top_10_commanders) {
  const container = document.getElementById("right-side-container");
  container.innerHTML = "";
  container.style = "";
  container.style.overflowY = "scroll";

  top_10_commanders.forEach((commanderData) => {
    const imgContainer = createImageContainer(commanderData);
    container.appendChild(imgContainer);
  });
}

function printCommanders() {
  console.log(top_10_commanders);
}
