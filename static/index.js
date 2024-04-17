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
var returned_commanders = {};

match_base_value = 2;
card_is_commander_value = 2;
high_synergy_value = 1;
high_inclusion_value = 1;

debug = true;

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
async function get_solo_commanders_from_scryfall(colors) {
  const solo_url = `https://api.scryfall.com/cards/search?q=id%3E%3D${colors}%20t%3Alegend%20t%3Acreature`;
  const response = await fetch(solo_url);
  if (response.status !== 200) {
    throw new Error(`Solo request failed with status code ${response.status}`);
  }

  const possible_commanders = await response.json();
  if (!possible_commanders.data) {
    throw new Error("No 'data' key in the solo response");
  }

  for (const commander of possible_commanders.data) {
    if (commander.legalities.commander === "legal") {
      returned_commanders[commander.name] = { data: commander, score: 0 };
    }
  }
}
// async function get_partner_commanders_from_scryfall(colors) {
//   const identity = colors.join(',');
//   const partners_url = `https://api.scryfall.com/cards/search?q=id%3A${identity}%20t%3Alegend%20t%3Acreature%20o%3A%22Partner%22%20%2Do%3A%22Partner%20with%22`;
//   const partner_response = await fetch(partners_url);
//   if (partner_response.status !== 200) {
//       throw new Error(`Partner request failed with status code ${partner_response.status}`);
//   }

//   const possible_partners = await partner_response.json();
//   if (!possible_partners.data) {
//       throw new Error("No 'data' key in the partner response");
//   }

//   for (const first_partner of possible_partners.data) {
//       if (first_partner.legalities.commander === 'legal') {
//           const deficit = colors.filter(color => !first_partner.color_identity.includes(color));
//           for (const second_partner of possible_partners.data) {
//               if (deficit.every(color => second_partner.color_identity.includes(color)) && second_partner.legalities.commander === 'legal') {
//                   const name_list = [first_partner.name, second_partner.name];
//                   const joined_name = name_list.sort().join(' + ');
//                   returned_commanders[joined_name] = {data: [first_partner, second_partner], score: 0};
//               }
//           }
//       }
//   }
// }
function format_name_for_edhrec(name) {
  const specials = "àáâãäåèéêëìíîïòóôõöùúûüýÿñç ";
  const replacements = "aaaaaaeeeeiiiiooooouuuuyync-";
  const removals = ",'.\"";

  let formatted_name = name
    .split("/")[0]
    .replace(" + ", " ")
    .trim()
    .toLowerCase();

  for (let i = 0; i < specials.length; i++) {
    formatted_name = formatted_name.replace(
      new RegExp(specials[i], "g"),
      replacements[i]
    );
  }

  for (let char of removals) {
    formatted_name = formatted_name.replace(new RegExp("\\" + char, "g"), "");
  }

  return formatted_name;
}
async function get_score_from_edhrec(commander_name, formatted_name, cards) {
  let score = 0;
  const url = `https://json.edhrec.com/pages/commanders/${formatted_name}.json`;

  const response = await fetch(url);
  if (response.status === 200) {
    const json_data = await response.json();
    if (json_data.cardlist) {
      const scored_cards = [];

      for (const card of cards) {
        if (card.name === commander_name) {
          score += card_is_commander_value;
        }

        for (const edhrec_card of json_data.cardlist) {
          if (card.name === edhrec_card.name) {
            score += match_base_value;

            if (edhrec_card.synergy >= 0.3) {
              score += high_synergy_value;
            }
            if (edhrec_card.num_decks / edhrec_card.potential_decks >= 0.4) {
              score += high_inclusion_value;
            }

            scored_cards.push(card.name);
          }
        }
      }

      returned_commanders[commander_name].score = Math.round(
        (score / cards.length) * 2.5
      );
      await new Promise((resolve) => setTimeout(resolve, 50));
    } else {
      if (debug) {
        console.log(
          `No data found for ${formatted_name} in return from EDHREC`
        );
      }
    }
  } else {
    if (debug) {
      console.log(`${formatted_name} not found at EDHREC.`);
    }
  }
}
function getUniqueColorIdentities(cards) {
  const colorIdentities = new Set();
  for (const card in cards) {
    if (cards.hasOwnProperty(card)) {
      for (const color of cards[card].color_identity) {
        colorIdentities.add(color);
      }
    }
  }
  console.log([...colorIdentities].join(""));
  return [...colorIdentities].join("");
}

function displayCommanders(sortedCommanders) {
  const container = document.getElementById("right-side-container");
  container.innerHTML = ""; // Clear the container

  let clickCount = 0; // Initialize click count

  sortedCommanders.forEach((commanderData, index) => {
    const img = document.createElement("img");

    if (commanderData.data.data.card_faces) {
      img.src = commanderData.data.data.card_faces[0].image_uris.png;
    } else {
      img.src = commanderData.data.data.image_uris.png;
    }

    img.style.position = "absolute";
    img.style.right = "0";
    img.style.zIndex = `${sortedCommanders.length - index}`; // Set initial z-index

    // Add event listener to the image
    img.addEventListener("click", function () {
      this.style.zIndex = "0"; // Decrease z-index by 1
      clickCount++; // Increment click count

      // If all cards have been clicked, reset z-index values and click count
      if (clickCount === sortedCommanders.length) {
        Array.from(container.children).forEach((img, i) => {
          img.style.zIndex = `${sortedCommanders.length - i}`;
        });
        clickCount = 0; // Reset click count
      }
    });

    container.appendChild(img);
  });
}

async function outputWinners(cards) {
  await get_solo_commanders_from_scryfall(getUniqueColorIdentities(cards));

  await Promise.all(
    Object.keys(returned_commanders).map(async (commander) => {
      await get_score_from_edhrec(
        returned_commanders[commander].data.name,
        format_name_for_edhrec(returned_commanders[commander].data.name),
        Object.values(cards)
      );
    })
  );

  sortedCommanders = Object.entries(returned_commanders)
    .sort((a, b) => b[1].score - a[1].score)
    .slice(0, 10)
    .map(([commander, data]) => ({ commander, data }));

  console.log(sortedCommanders);
  displayCommanders(sortedCommanders);
}

function printCommanders() {
  console.log(returned_commanders);
}
