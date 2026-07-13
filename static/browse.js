// Creates two variables. One for the search bar and the other is the grid the band cards are in
const searchBar = document.querySelector('input[name="band-search-bar"]');
const bandGrid = document.querySelector('.band-grid');

const locationSearchBar = document.querySelector('input[name="location-search-bar"]');

// The function that dynamically gets the bands from the database to display
function fetchBands() {
    // Gets the search bar from the page
    const search = document.getElementById("band-search-bar").value;
    // Finds the genre checkboxes and generates an array of checked genres
    const checkedGenres = Array.from(document.querySelectorAll('.genre-checkbox:checked'))
        .map(checkbox => checkbox.value)
        .join(',');
    const locationSearch = document.getElementById("location-search-bar").value;

    // Fetch is what a
    fetch(`/api/bands?band-search=${search}&genres=${checkedGenres}&location=${locationSearch}`)
        // Once the api response is back it converts it from json to a js object
        .then(response => response.json())
        // This runs once the api response has been turned into an object
        .then(bands => {
            // Clears the grid of band cards
            bandGrid.innerHTML = '';
            // Loops through each band returned and displays the band card for each one
            bands.forEach(band => {
                bandGrid.innerHTML += `
                    <div class="band-card" onclick="window.location.href='/band/${band.id}'">
                        <h3>${band.band_name}</h3>
                        <p>Genre: ${band.genre}</p>
                        <p>Location: ${band.location}</p>
                        <p>Rating: ${Math.round(band.likes / (band.likes + band.dislikes + 1) * 100)}</p>
                    </div>
                `;
            });
        });
}

// The event listener listens to the search bar and runs the fetchBands function when it changes
searchBar.addEventListener('input', fetchBands);
// Adds an event listener to every genre checkbox to allow the code to detect when it has been checked
document.querySelectorAll('.genre-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', fetchBands);
});
// Adds an event listener to the location filter to allow that to work
locationSearchBar.addEventListener('input', fetchBands);

// Allows the genre selection panel to drop down
const genreBtn = document.getElementById("genre-filter-button");
const genrePanel = document.getElementById("genre-panel");

genreBtn.addEventListener("click", () => {
    if (genrePanel.style.display === "none") {
        genrePanel.style.display = "block";
        genreBtn.textContent = "Select Genre ▶";
    } else {
        genrePanel.style.display = "none";
        genreBtn.textContent = "Select Genres ▼";
    }
});