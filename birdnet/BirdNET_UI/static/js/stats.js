var birds = null;
var eBirds = null;
var birdCards = null;

async function fetchConfidenceThreshold() {
    try {
        const response = await fetch('/api/birds_config/');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        confidence_threshold = parseFloat(data.confidence_threshold);
        return confidence_threshold;
    } catch (error) {
        console.error('Error fetching confidence threshold:', error);
    }   
}
var confidence_threshold = fetchConfidenceThreshold();

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

// Bird card class for displaying bird information
class BirdCard {
    constructor(bird, confidenceThreshold) {
        this.bird = bird;
        this.confidenceThreshold = confidenceThreshold;
        this.element = this.createCardElement();
    }

    createCardElement() {
        const cardElement = document.createElement('div');
        cardElement.className = 'bird-card';
        
        // Add inactive class for birds with count 0
        if (this.bird.count === 0) {
            cardElement.classList.add('inactive');
        }
        
        // Add low-confidence class for birds with confidence below threshold but count > 0
        if (this.bird.max_confidence && 
            this.bird.max_confidence < this.confidenceThreshold && 
            this.bird.count > 0) {
            cardElement.classList.add('low-confidence');
        }
        
        // Determine image source
        const imageUrl = this.bird.image || '/static/img/bird_not_found.png';
                
        // Create card content with rarity bubble
        const rarityText = this.formatRarity(this.bird.rarity);
        let rarityClass = 'rarity';
        if (rarityText === 'Extremely Rare') rarityClass += ' extremely-rare';
        else if (rarityText === 'Very Rare') rarityClass += ' very-rare';
        else if (rarityText === 'Rare') rarityClass += ' rare';
        else if (rarityText === 'Uncommon') rarityClass += ' uncommon';
        else if (rarityText === 'Common') rarityClass += ' common';
        else if (rarityText === 'Very Common') rarityClass += ' very-common';
        else if (rarityText === 'Abundant') rarityClass += ' abundant';
        const rarityBubble = `<div class="rarity-bubble ${rarityClass}"></div>`;

        // Create count bubble
        const countText = this.bird.count || 0;
        let countBubble = '';
        if (countText > 0) {
            countBubble = `<div class="count-bubble">${countText}</div>`;
        }
        
        // Format max confidence display
        const confidenceText = (this.bird.max_confidence * 100).toFixed(1);
        let confidenceBubble = '';
        if (this.bird.max_confidence !== undefined && this.bird.max_confidence !== null) {
            const confidenceClass = (this.bird.max_confidence < this.confidenceThreshold) ? 'max-confidence below-threshold confidence-bubble' : 'max-confidence confidence-bubble';
            confidenceBubble = `<div class="${confidenceClass}">Confidence: ${confidenceText}%</div>`;
        }
        
        cardElement.innerHTML = `
            <div class="bird-image-container">
                <img src="${imageUrl}" alt="${this.bird.common_name}" onerror="this.src='/static/img/bird_not_found.png'">
                ${rarityBubble}
                ${countBubble}
                ${confidenceBubble}
            </div>
            <div class="bird-info">
                <h3>${this.bird.common_name}</h3>
                <p class="scientific-name">${this.bird.scientific_name}</p>
            </div>
        `;
        
        // Add click event to open modal
        cardElement.addEventListener('click', () => {
            this.openBirdModal();
        });
        
        return cardElement;
    }
    
    formatRarity(rarity) {
        // Format rarity value for display
        if (rarity === null || rarity === undefined) return 'Unknown';
        
        // Convert rarity to a descriptive text
        if (rarity === 0) return 'Extremely Rare';
        if (rarity < 10) return 'Very Rare';
        if (rarity < 50) return 'Rare';
        if (rarity < 200) return 'Uncommon';
        if (rarity < 500) return 'Common';
        if (rarity < 1000) return 'Very Common';
        return 'Abundant';
    }
    
    openBirdModal() {
        // Set basic bird information
        document.getElementById('modalBirdName').textContent = this.bird.common_name;
        document.getElementById('modalScientificName').textContent = this.bird.scientific_name;
        
        // Fetch data for the charts
        this.fetchHourlyCounts();
        this.fetchWeeklyCounts();
        
        // Set bird image
        const birdImage = document.getElementById('modalBirdImage');
        birdImage.src = this.bird.image || '/static/img/bird_not_found.png';
        birdImage.alt = this.bird.common_name;
        
        // Fetch additional bird data from ebirds_extra
        fetch(`/api/ebirds_extra/${encodeURIComponent(this.bird.scientific_name)}/`)
            .then(response => response.json())
            .then(extraData => {
                if (extraData) {
                    // Set audio if available
                    const audioPlayer = document.getElementById('modalBirdAudio');
                    const bestRecordingPlayer = document.getElementById('bestRecordingAudio');
                    
                    if (extraData.ideal_audio) {
                        audioPlayer.src = extraData.ideal_audio;
                    } 
                    
                    // Set best recording if available
                    if (extraData.best_recording) {
                        bestRecordingPlayer.src = extraData.best_recording;
                    } 
                    
                    // Set range map if available
                    const rangeMap = document.getElementById('modalRangeMap');
                    if (extraData.range_map) {
                        rangeMap.src = extraData.range_map;
                    } 
                    
                    // Set migration description
                    document.getElementById('migrationDescription').textContent = 
                        extraData.migration_description || 'No migration information available.';
                    
                    // Set bird description
                    document.getElementById('modalDescription').innerHTML = 
                        extraData.description || 'No description available.';
                    
                    // Set habitat and diet information
                    document.getElementById('habitatDescription').innerHTML = 
                        extraData.habitat_value || 'No habitat information available.';
                    document.getElementById('foodDescription').innerHTML = 
                        extraData.food_value || 'No diet information available.';
                    
                    // Set behavior information
                    document.getElementById('behaviorDescription').innerHTML = 
                        extraData.behavior_value || 'No behavior information available.';
                    document.getElementById('nestingDescription').innerHTML = 
                        extraData.nesting_value || 'No nesting information available.';
                    document.getElementById('findThisBird').innerHTML = 
                        extraData.find_this_bird || 'No information available on finding this bird.';
                    document.getElementById('backyardTips').innerHTML = 
                        extraData.tips || 'No backyard tips available.';
                    
                    // Set conservation information
                    document.getElementById('conservationDescription').innerHTML = 
                        extraData.conservation_value || 'No conservation information available.';
                    
                    // Set summary icons
                    document.getElementById('habitatValue').textContent = 
                        this.getSummaryText(extraData.habitat_value) || 'Unknown';
                    document.getElementById('foodValue').textContent = 
                        this.getSummaryText(extraData.food_value) || 'Unknown';
                    document.getElementById('nestingValue').textContent = 
                        this.getSummaryText(extraData.nesting_value) || 'Unknown';
                    document.getElementById('behaviorValue').textContent = 
                        this.getSummaryText(extraData.behavior_value) || 'Unknown';
                    document.getElementById('conservationValue').textContent = 
                        this.getSummaryText(extraData.conservation_value) || 'Unknown';

                    // Set corresponding images (if you have specific URLs in extraData)
                    document.getElementById('habitatIcon').src = this.getIcon('habitat', extraData.habitat_value);
                    document.getElementById('foodIcon').src = this.getIcon('food', extraData.food_value);
                    document.getElementById('nestingIcon').src = this.getIcon('nesting', extraData.nesting_value);
                    document.getElementById('behaviorIcon').src = this.getIcon('behavior', extraData.behavior_value);
                    document.getElementById('conservationIcon').innerHTML = this.generateConservationIcon(extraData.conservation_value);
                }
            })
            .catch(error => {
                console.error('Error fetching bird extra data:', error);
            });
        
        // Show the modal
        document.getElementById('birdModal').style.display = 'block';
    }
    
    getSummaryText(text) {
        if (!text) return null;
        
        // Try to get the first sentence or phrase
        const firstSentence = text.split(/[.!?]/).filter(s => s.trim().length > 0)[0];
        if (firstSentence && firstSentence.length < 30) {
            return firstSentence.trim();
        }
        
        // If first sentence is too long, return a shorter version
        return firstSentence ? firstSentence.substring(0, 25) + '...' : null;
    }
    
    fetchHourlyCounts() {
        fetch(`/api/hourly_counts/${encodeURIComponent(this.bird.scientific_name)}/`)
            .then(response => response.json())
            .then(data => {
                // Create hourly counts chart
                this.createHourlyChart(data);
            })
            .catch(error => {
                console.error('Error fetching hourly counts:', error);
                document.getElementById('hourlyCountsChart').innerHTML = 
                    '<p class="no-data">No hourly data available for this bird</p>';
            });
    }
    
    fetchWeeklyCounts() {
        fetch(`/api/weekly_counts/${encodeURIComponent(this.bird.scientific_name)}/`)
            .then(response => response.json())
            .then(data => {
                // Create weekly counts chart
                this.createWeeklyChart(data);
            })
            .catch(error => {
                console.error('Error fetching weekly counts:', error);
                document.getElementById('weeklyCountsChart').innerHTML = 
                    '<p class="no-data">No weekly data available for this bird</p>';
            });
    }

    createHourlyChart(data) {
        const hours = Array.from({ length: 24 }, (_, i) => i);
        const trace = {
            x: hours,
            y: data.hourly_counts,
            type: 'bar',
            marker: {
                color: 'rgba(0, 171, 219, 0.6)',
            },
        };

        const layout = {
            title: {
                text: 'Observations Per Hour of the Day',
                font: {
                    size: 16,
                }
            },
            xaxis: {
                title: {
                    text: 'Time of Day',
                    font: {
                        size: 14,
                        color: '#333'
                    },
                    standoff: 15 // Distance between axis and title
                },
                tickvals: hours,
                ticktext: hours.map(hour => `${hour}`),
                tickangle: 0,
            },
            yaxis: {
                title: {
                    text: '# Observations',
                    font: {
                        size: 14,
                        color: '#333'
                    },
                    standoff: 15 // Distance between axis and title
                },
            },
            margin: {
                l: 70,  // Left margin for y-axis title
                r: 20,  // Right margin
                t: 60,  // Top margin for chart title
                b: 70   // Bottom margin for x-axis title
            },
            autosize: true
        };

        Plotly.newPlot('hourlyCountsChart', [trace], layout);
    }

    createWeeklyChart(data) {
        const weeks = Array.from({ length: 52 }, (_, i) => i + 1);
        
        // Define month boundaries (approximate week numbers for month starts)
        const monthBoundaries = [1, 5, 9, 14, 18, 22, 27, 31, 35, 40, 44, 48];
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        const trace = {
            x: weeks,
            y: data,
            type: 'bar',
            marker: {
                color: 'rgba(255, 0, 0, 0.6)',
            },
        };

        const layout = {
            title: {
                text: 'Total Observations Per Week of the Year',
                font: {
                    size: 16,
                }
            },
            xaxis: {
                title: {
                    text: 'Month',
                    font: {
                        size: 14,
                        color: '#333'
                    },
                    standoff: 15 // Distance between axis and title
                },
                tickvals: monthBoundaries,
                ticktext: monthNames,
                tickangle: 0,
            },
            yaxis: {
                title: {
                    text: '# Observations',
                    font: {
                        size: 14,
                        color: '#333'
                    },
                    standoff: 15 // Distance between axis and title
                },
            },
            margin: {
                l: 70,  // Left margin for y-axis title
                r: 20,  // Right margin
                t: 60,  // Top margin for chart title
                b: 70   // Bottom margin for x-axis title
            },
            autosize: true
        };

        Plotly.newPlot('weeklyCountsChart', [trace], layout);
    }

    getIcon(category, value) {
        value = value.toLowerCase();
        value = value.replace(/\s+/g, '_');

        switch (category) {
            case 'habitat':
                switch(value) {
                    case 'deserts':
                        return '/static/img/habitat/deserts.jpg';
                    case 'forests':
                        return '/static/img/habitat/forests.jpg';
                    case 'grasslands':
                        return '/static/img/habitat/grasslands.jpg';
                    case 'lakes_and_ponds':
                        return '/static/img/habitat/lakes_and_ponds.jpg';
                    case 'marshes':
                        return '/static/img/habitat/marshes.jpg';
                    case 'oceans':
                        return '/static/img/habitat/oceans.jpg';
                    case 'open_woodlands':
                        return '/static/img/habitat/open_woodlands.jpg';
                    case 'rivers_and_streams':
                        return '/static/img/habitat/rivers_and_streams.jpg';
                    case 'scrub':
                        return '/static/img/habitat/scrub.jpg';
                    case 'shorelines':
                        return '/static/img/habitat/shorelines.jpg';
                    case 'towns':
                        return '/static/img/habitat/towns.jpg';
                    case 'tundra':
                        return '/static/img/habitat/tundra.jpg';    
                    default:
                        console.error("Failed to find icon for habitat:", value);
                        return null;
                }
            case 'food':
                switch(value) {
                    case 'aquatic_invertibrates':
                        return '/static/img/food/aquatic_invertibrates.jpg';
                    case 'birds':
                        return '/static/img/food/birds.jpg';
                    case 'carrion':
                        return '/static/img/food/carrion.jpg';
                    case 'fish':
                        return '/static/img/food/fish.jpg';
                    case 'fruit':
                        return '/static/img/food/fruit.jpg';
                    case 'insects':
                        return '/static/img/food/insects.jpg';
                    case 'mammals':
                        return '/static/img/food/mammals.jpg';
                    case 'nectar':
                        return '/static/img/food/nectar.jpg';
                    case 'omnivore':
                        return '/static/img/food/omnivore.jpg';
                    case 'plants':
                        return '/static/img/food/plants.jpg';
                    case 'seeds':
                        return '/static/img/food/seeds.jpg';
                    case 'small_animals':
                        return '/static/img/food/small_animals.jpg';
                    default:
                        console.error("Failed to find icon for food:", value);
                        return null;
                }
            case 'nesting':
                switch(value) {
                    case 'building':
                        return '/static/img/nesting/building.jpg';
                    case 'burrow':
                        return '/static/img/nesting/burrow.jpg';
                    case 'cavity':
                        return '/static/img/nesting/cavity.jpg';
                    case 'cliff':
                        return '/static/img/nesting/cliff.jpg';
                    case 'floating':
                        return '/static/img/nesting/floating.jpg';
                    case 'ground':
                        return '/static/img/nesting/ground.jpg';
                    case 'shrub':
                        return '/static/img/nesting/shrub.jpg';
                    case 'tree':
                        return '/static/img/nesting/tree.jpg';
                    default:    
                        console.error("Failed to find icon for nesting:", value);
                        return null;
                }
            case 'behavior':
                switch(value) {
                    case 'aerial_dive':
                        return '/static/img/behavior/aerial_dive.jpg';
                    case 'aerial_forager':
                        return '/static/img/behavior/aerial_forager.jpg';
                    case 'bark_forager':
                        return '/static/img/behavior/bark_forager.jpg';
                    case 'dabbler':
                        return '/static/img/behavior/dabbler.jpg';
                    case 'flycatching':
                        return '/static/img/behavior/flycatching.jpg';
                    case 'foliage_gleaner':
                        return '/static/img/behavior/foliage_gleaner.jpg';
                    case 'ground_forager':
                        return '/static/img/behavior/ground_forager.jpg';
                    case 'hovering':
                        return '/static/img/behavior/hovering.jpg';
                    case 'probing':
                        return '/static/img/behavior/probing.jpg';
                    case 'soaring':
                        return '/static/img/behavior/soaring.jpg';
                    case 'stalking':
                        return '/static/img/behavior/stalking.jpg';
                    case 'surface_dive':
                        return '/static/img/behavior/surface_dive.jpg';
                    default:
                        console.error("Failed to find icon for behavior:", value);
                        return null;
                }
            default:
                console.error("Failed to find icon for category:", category, "with value:", value);
                return null;
        }
    }

    generateConservationIcon(value) {
        // Low Concern
        // Least Concern
        // Restricted Range
        // Declining
        // Red Watch List
        // Common Bird in Steep Decline
        // Vulnerable
        // Near Threatened
        
        let text = value;
        value = value.replace(/\s+/g, '');
        value = value.toLowerCase();

        let color = 'gray';
        let fgColor = 'white';
        switch(value) {
            case 'lowconcern':
                text = 'Low Concern';
                color = 'rgb(95, 154, 13)';
                fgColor = 'black';
                break;
            case 'leastconcern':
                text = 'Least Concern';
                color = 'rgb(112, 156, 50)';
                fgColor = 'black';
                break;
            case 'restrictedrange':
                text = 'Restricted';
                color = 'rgb(203, 179, 19)';
                fgColor = 'black';
                break;
            case 'declining':
                text = 'Declining';
                color = 'rgb(184, 134, 11)';
                fgColor = 'black';
                break;
            case 'redwatchlist':
                text = 'Watch List';
                color = 'rgb(184, 57, 11)';
                fgColor = 'white';
                break;
            case 'commonbirdinsteepdecline':
                text = 'Steep Decline';
                color = 'rgb(141, 13, 13)';
                fgColor = 'white';
                break;
            case 'vulnerable':
                text = 'Critical';
                color = 'rgb(130, 25, 13)';
                fgColor = 'white';
                break;
            case 'nearthreatened':
                text = 'Threatened';
                color = 'rgb(163, 12, 12)';
                fgColor = 'white';
                break;
            default:
                text = 'Unknown';
                color = 'rgb(139, 139, 139)';
                fgColor = 'black';
                break;
        }

        // create a html div with the text and background color based on the text
        const conservationIcon = document.createElement('div');
        conservationIcon.textContent = text;
        conservationIcon.style.backgroundColor = color;
        conservationIcon.style.color = fgColor;
        // conservationIcon.style.padding = '5px';
        conservationIcon.style.borderRadius = '5px';
        conservationIcon.style.display = 'flex';
        conservationIcon.style.alignItems = 'center';
        conservationIcon.style.justifyContent = 'center';
        conservationIcon.style.overflowWrap = 'break-word';
        conservationIcon.style.wordBreak = 'break-word';
        conservationIcon.style.maxWidth = '60px';
        conservationIcon.style.maxHeight = '60px';
        conservationIcon.style.textAlign = 'center';
        conservationIcon.style.fontSize = '0.8em';
        conservationIcon.style.width = '100%';
        conservationIcon.style.height = '100%';
        
        return conservationIcon.outerHTML;
    }
}

// Bird collection class for managing the display of multiple bird cards
class BirdCollection {
    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector);
        this.birds = [];
        this.eBirds = [];
        this.birdDetections = [];
        this.mergedBirds = [];
        this.cards = [];
        this.sortField = 'count';
        this.sortDirection = 'desc';
        this.filterText = '';
        this.confidenceThreshold = 0.65; // Default value, will be updated
    }
    
    async loadBirds() {
        try {
            // Show loading state
            this.container.innerHTML = '<p class="loading-message">Loading birds...</p>';
            
            // Fetch confidence threshold and birds from all sources in parallel
            const [statsResponse, eBirdsResponse, detectionsResponse] = await Promise.all([
                fetch('/api/observation_stats/'),
                fetch('/api/ebirds/'),
                fetch('/api/bird_detections_count/')
            ]);
            
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                this.confidenceThreshold = parseFloat(statsData.confidence_threshold);
                console.log("Config Statistics Data: ", statsData);
            } else {
                throw new Error('Failed to fetch observation stats');
            }

            if (!eBirdsResponse.ok || !detectionsResponse.ok) {
                throw new Error('Failed to fetch birds data');
            }
            
            // Parse the responses
            this.eBirds = await eBirdsResponse.json();
                // 'scientific_name',
                // 'common_name',
                // 'rarity',
                // 'image'
            this.birdDetections = await detectionsResponse.json();
                // 'scientific_name',
                // 'common_name',
                // 'total_detections',
                // 'max_confidence'

            this.mergedBirds = {};        
            this.eBirds.forEach(eBird => {
                const detectionData = this.birdDetections.find(bird => bird.scientific_name === eBird.scientific_name);

                this.mergedBirds[eBird.scientific_name] = {
                    scientific_name: eBird.scientific_name,
                    common_name: eBird.common_name,
                    count: detectionData ? detectionData.total_detections : 0,
                    max_confidence: detectionData ? detectionData.max_confidence : null,
                    rarity: eBird.rarity,
                    image: eBird.image,
                };
            });
            this.mergedBirds = Object.values(this.mergedBirds);
            // console.log("mergedBirds: ", this.mergedBirds);
                        
            // Render the merged birds
            this.render();
        } catch (error) {
            console.error('Error loading birds:', error);
            this.container.innerHTML = '<p class="error-message">Failed to load birds. Please try again later.</p>';
        }
    }    
    
    render() {
        // Clear container
        this.container.innerHTML = '';
        this.cards = [];
        
        // Filter and sort birds
        const filteredBirds = this.filterBirds();
        const sortedBirds = this.sortBirds(filteredBirds);
        
        // Create and append cards
        sortedBirds.forEach(bird => {
            const card = new BirdCard(bird, this.confidenceThreshold);
            this.cards.push(card);
            this.container.appendChild(card.element);
        });
        
        // Update count display
        document.getElementById('bird-count').textContent = `Showing ${sortedBirds.length} of ${this.mergedBirds.length} birds`;
    }
    
    filterBirds() {
        if (!this.filterText) return this.mergedBirds;
        
        const searchTerm = this.filterText.toLowerCase();
        return this.mergedBirds.filter(bird => 
            bird.common_name.toLowerCase().includes(searchTerm) || 
            bird.scientific_name.toLowerCase().includes(searchTerm)
        );
    }
    
    sortBirds(birds) {
        return [...birds].sort((a, b) => {
            let valueA = a[this.sortField];
            let valueB = b[this.sortField];
            
            // Handle null values
            if (valueA === null) valueA = this.sortField === 'rarity' ? Infinity : '';
            if (valueB === null) valueB = this.sortField === 'rarity' ? Infinity : '';
            
            // Compare based on type
            let comparison;
            if (typeof valueA === 'number') {
                comparison = valueA - valueB;
            } else {
                comparison = String(valueA).localeCompare(String(valueB));
            }
            
            // Apply sort direction
            return this.sortDirection === 'asc' ? comparison : -comparison;
        });
    }
    
    setSortField(field) {
        if (this.sortField === field) {
            // Toggle direction if same field
            this.toggleSortDirection();
        } else {
            // Set new field and default to descending for count and rarity, ascending for names
            this.sortField = field;
            if (field === 'count' || field === 'rarity') {
                this.sortDirection = 'desc'; // Higher values first for count and rarity
            } else {
                this.sortDirection = 'asc'; // A-Z for names
            }
        }
        
        this.render();
        
        // Update the sort icon
        const sortIcon = document.querySelector('.sort-icon');
        if (sortIcon) {
            sortIcon.textContent = this.sortDirection === 'asc' ? '↑' : '↓';
        }
    }
    
    toggleSortDirection() {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        this.render();
    }
    
    setFilterText(text) {
        this.filterText = text;
        this.render();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize bird collection
    const birdCollection = new BirdCollection('#bird-cards-container');
    birdCollection.loadBirds();
    
    // Set up sorting
    const sortSelect = document.getElementById('sort-select');
    sortSelect.value = 'count';
    
    sortSelect.addEventListener('change', function() {
        birdCollection.setSortField(this.value);
    });
    
    // Set up sort direction toggle and initialize with descending icon
    const sortDirectionButton = document.getElementById('sort-direction');
    const sortIcon = sortDirectionButton.querySelector('.sort-icon');
    sortIcon.textContent = '↓';
    
    sortDirectionButton.addEventListener('click', function() {
        birdCollection.toggleSortDirection();
        // Update the sort icon
        sortIcon.textContent = birdCollection.sortDirection === 'asc' ? '↑' : '↓';
    });
    
    // Set up filtering
    document.getElementById('search-input').addEventListener('input', function() {
        birdCollection.setFilterText(this.value);
    });
    
    // Set up tab functionality for modal
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons and content
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab') + '-tab';
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Close modal when clicking the close button
    document.querySelector('.close').addEventListener('click', function() {
        document.getElementById('birdModal').style.display = 'none';
    });
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('birdModal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});
