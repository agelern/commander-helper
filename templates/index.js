function addItem() {
  var list = document.getElementById("listOfNames");
  var name = document.getElementById("search-bar").value;
  var entry = document.createElement("li");

  var deleteButton = document.createElement("button");
  deleteButton.addEventListener("click", removeItem);
  deleteButton.textContent = "X";

  entry.appendChild(document.createTextNode(name));
  entry.appendChild(deleteButton);
  list.appendChild(entry);
}

function removeItem() {
  this.parentElement.remove();
}
