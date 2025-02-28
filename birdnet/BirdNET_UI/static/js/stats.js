const socket = new WebSocket('ws://localhost:8150/ws/birds/');  // Adjust the URL as necessary

var birds = null;
var eBirds = null;
var birdCards = null;

async function fetchBirdDetectionsCount() {
    try {
        const response = await fetch('/api/bird_detections_count/');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        birds = data;  
    } catch (error) {
        console.error('Error fetching bird detections count:', error);
    }
}

async function fetchEBirds() {
    try {
        const response = await fetch('/api/ebirds/');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        eBirds = data;  
    } catch (error) {
        console.error('Error fetching eBirds:', error);
    }
}

class birdCard {
    constructor(common_name, scientific_name, rarity, image, count, max_confidence) {
        this.common_name = common_name;
        this.scientific_name = scientific_name;
        this.rarity = rarity;
        this.image = image;
        this.count = count;
        this.max_confidence = max_confidence;
    }

    getCard() {
        var cardElement = document.createElement('div');
        cardElement.classList.add('birdCard');
        cardElement.classList.add('grid-item');
        var confidence_html = ``;
        if (this.count == 0) {
            cardElement.classList.add('greyed-out');
        } else {
            confidence_html = `
                <p class="max-confidence">Conf: ${this.max_confidence}</p>
                <img class="speaker_icon" src="/static/img/Speaker_Icon.png" alt="play audio clip"></img>
            `;
        }
        var img_rarity = "/static/img/rarity_rare.png";

        if (this.rarity > 1000) {
            img_rarity = "/static/img/rarity_common.png";
        } else if (this.rarity > 20) {
            img_rarity = "/static/img/rarity_uncommon.png";
        }

        const card_html = `
            <h3>${this.common_name}</h3>
            <p><em>${this.scientific_name}</em></p>
            <img class="grid_image" src="${this.image}" alt="${this.common_name}">
            <img class="rarity_img" src="${img_rarity}" alt="Rarity = ${this.rarity}">
            <p class="detection-count">Detections: ${this.count}</p>
            ${confidence_html}
        `;
        cardElement.innerHTML = card_html;

        // Add click event to open modal
        cardElement.addEventListener('click', () => {
            this.openModal();
        });

        return cardElement;
    }

    openModal() {
        const modal = document.getElementById('bird-modal');
        document.getElementById('modal-bird-name').textContent = this.common_name;
        document.getElementById('modal-bird-scientific-name').textContent = this.scientific_name;

        // Fetch data for the charts
        this.fetchHourlyCounts();
        this.fetchWeeklyCounts();

        modal.style.display = "block"; // Show the modal
        this.addCloseEvent(modal);
    }

    async fetchHourlyCounts() {
        try {
            const response = await fetch(`/api/hourly_counts/${this.scientific_name}/`); // Adjust the API endpoint
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            this.renderHourlyCountChart(data);
        } catch (error) {
            console.error('Error fetching hourly counts:', error);
        }
    }

    async fetchWeeklyCounts() {
        try {
            const response = await fetch(`/api/weekly_counts/${this.scientific_name}/`); // Adjust the API endpoint
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            this.renderWeeklyCountChart(data);
        } catch (error) {
            console.error('Error fetching weekly counts:', error);
        }
    }

    addCloseEvent(modal) {
        const closeButton = modal.querySelector('.close-button');
        closeButton.onclick = function() {
            modal.style.display = "none"; // Hide the modal
        };

        // Close the modal when clicking outside of it
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = "none"; // Hide the modal
            }
        };
    }

    renderHourlyCountChart(data) {
        console.log("renderHourlyCountChart data:", data.hourly_counts);

        // Create an array of hours (0-23)
        const hours = Array.from({ length: 24 }, (_, i) => i);

        const trace = {
            x: hours, // Use the array of hours as x values
            y: data.hourly_counts, // Use the hourly counts as y values
            type: 'bar',
            marker: {
                color: 'rgba(0, 171, 219, 0.6)',
            },
        };

        const layout = {
            title: 'Total Occurrences Per Hour',
            xaxis: {
                title: 'Time of Day',
                tickvals: hours, // Optional: Set tick values to match the hours
                ticktext: hours.map(hour => `${hour}:00`), // Optional: Format tick labels
            },
            yaxis: {
                title: 'Total Counts',
            },
        };

        Plotly.newPlot('hourly-count-chart', [trace], layout);
    }

    renderWeeklyCountChart(data) {
        console.log("renderWeeklyCountChart data:", data);

        const weeks = Array.from({ length: 52 }, (_, i) => i + 1);
        const trace = {
            x: weeks, // Assuming data.weeks contains the week numbers
            y: data, // Assuming data.counts contains the total counts per week
            type: 'bar',
            marker: {
                color: 'rgba(255, 0, 0, 0.6)',
            },
        };

        const layout = {
            title: 'Total Counts Per Week of the Year',
            xaxis: {
                title: 'Week of the Year',
                tickvals: weeks, // Optional: Set tick values to match the hours
                ticktext: weeks.map(week => `Week ${week}`), // Optional: Format tick labels
            },
            yaxis: {
                title: 'Total Counts',
            },
        };

        Plotly.newPlot('weekly-count-chart', [trace], layout);
    }
}

function mergeBirds() {
    if (!birds || !eBirds) {
        console.error('Birds or eBirds data is not available');
        return [];  // Return an empty array or handle the error appropriately
    }

    var birdCards = [];
    for (var i = 0; i < eBirds.length; i++) {
        var ebird = eBirds[i];
        if (ebird.common_name.includes("(hybrid)")) {
            continue;
        }
        var bird = birds.find(b => b.scientific_name === ebird.scientific_name);
        if (bird) {
            birdCards.push(new birdCard(common_name = bird.common_name, scientific_name = ebird.scientific_name, rarity = ebird.rarity, image = ebird.image, count = bird.total_detections, max_confidence = Math.round(bird.max_confidence * 1000) / 1000));
        } else {
            birdCards.push(new birdCard(common_name = ebird.common_name, scientific_name = ebird.scientific_name, rarity = ebird.rarity, image = ebird.image, count = 0, max_confidence = 0));
        }
    }
    return birdCards;
}

window.onload = async function() {
    await Promise.all([
        fetchBirdDetectionsCount(),
        fetchEBirds()
    ]);

    birdCards = mergeBirds();
    console.log("birdCards:", birdCards);
    
    // Clear existing bird cards before appending new ones
    const birdCardsContainer = document.getElementById('bird-cards');
    birdCardsContainer.innerHTML = '';  // Clear existing cards

    // Display the bird cards
    displayBirdCards(birdCards);

    // Add event listener for sorting
    document.getElementById('sort-options').addEventListener('change', function() {
        sortBirdCards();
    });

    document.getElementById('sort-order').addEventListener('change', function() {
        sortBirdCards();
    });
};

function displayBirdCards(cards) {
    const birdCardsContainer = document.getElementById('bird-cards');
    birdCardsContainer.innerHTML = '';  // Clear existing cards

    for (var i = 0; i < cards.length; i++) {
        var card = cards[i];
        var cardElement = card.getCard();
        birdCardsContainer.appendChild(cardElement);
    }
}

function sortBirdCards() {
    const sortBy = document.getElementById('sort-options').value;
    const sortOrder = document.getElementById('sort-order').value;

    switch (sortBy) {
        case 'common_name':
            birdCards.sort((a, b) => a.common_name.localeCompare(b.common_name));
            break;
        case 'scientific_name':
            birdCards.sort((a, b) => a.scientific_name.localeCompare(b.scientific_name));
            break;
        case 'rarity':
            birdCards.sort((a, b) => a.rarity - b.rarity);
            break;
        case 'count':
            birdCards.sort((a, b) => a.count - b.count);
            break;
    }

    // Reverse the order if descending is selected
    if (sortOrder === 'desc') {
        birdCards.reverse();
    }

    displayBirdCards(birdCards); // Refresh the display after sorting
}

function promptForPassword(event) {
    event.preventDefault(); // Prevent the default action
    const password = prompt("Please enter the password to compile:");
    const correctPassword = "birdnet"; // Change this to your desired password

    if (password === correctPassword) {
        window.location.href = "/api/compile_ebirds/"; // Redirect to the compile URL
    } else {
        alert("Access denied.");
    }
}