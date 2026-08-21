function filterCards() {
  // Get what the user types in the search box
  const query = document
    .getElementById("searchInput")
    .value.toLowerCase()
    .trim();

  // Get all package cards
  const cards = document.querySelectorAll(".package-card");

  // Get the hero section
  const hero = document.querySelector(".hero");

  // Get the "No destinations found" message
  const noResults = document.getElementById("noResults");

  // Get the packages heading
  const title = document.querySelector(".section-title");

  // Get the packages section
  const section = document.querySelector(".packages-section");

  // Get the package grid
  const grid = document.getElementById("packagesGrid");

  // Count how many packages match
  let visible = 0;

  // Hide hero section while searching
  if (query !== "") {
    hero.style.display = "none";
  } else {
    hero.style.display = "flex";
  }

  // Check each package card
  cards.forEach((card) => {
    // Get ONLY the destination/package name
    const destination = card
      .querySelector("h3")
      .textContent.toLowerCase()
      .trim();

    // Check if the typed letters exist anywhere in the destination name
      if (destination.startsWith(query)) {
          // Show the matching package
          card.style.display = "block";

          // Increase matching package count
          visible++;
        } else {
          // Hide the package if it doesn't match
          card.style.display = "none";
        }
  });

  // If no package matches
  if (visible === 0) {
    // Show "No destinations found"
    noResults.style.display = "block";

    // Hide packages heading
    title.style.display = "none";

    // Hide package grid
    grid.style.display = "none";

    // Reduce empty space
    section.style.padding = "20px 0";
  } else {
    // Hide "No destinations found"
    noResults.style.display = "none";

    // Show packages heading
    title.style.display = "block";

    // Show package grid
    grid.style.display = "grid";

    // Restore normal spacing
    section.style.padding = "0 48px 64px";
  }
}
