const socket = new WebSocket('ws://localhost:8151/ws/birds/');  // Adjust the URL as necessary
function connectWebSocket() {
    socket.onopen = function(event) {
        console.log("WebSocket is open now!");
    };

    socket.onmessage = function(event) {
        // console.log("WebSocket message received:", event.data);        
        let message;
        try {
            message = JSON.parse(event.data);
        } catch (error) {
            console.error("Failed to parse JSON:", error);
            console.log("Received data:", event.data);  // Log the raw data for debugging
            return;  // Exit the function if parsing fails
        }
        
        if (message.data.update === "True") {
            console.log("Bird update received: WS");
            updateAll();
        } else {
            console.log("Bad update received");
            console.log(data);  // Log the parsed data
        }
    };

    socket.onclose = function(event) {
        console.log("WebSocket is closed now.");
    };

    socket.onerror = function(error) {
        console.error("WebSocket error: ", error);
    };
}
connectWebSocket();



let heatmapChart; // Declare the heatmapChart variable globally



// Function to fetch bird records
async function fetchBirds() {
    try {
        fetch('/api/birds/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }).then(data => {
            console.log("fetchBirds: ", data); // Handle the data from the API
            // do something with the data
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
        
    } catch (error) {
        console.error('Error fetching birds:', error);
    }
}
async function fetchBirdsNow() {
    try {
        fetch('/api/birds_now/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            return response.json();
        }).then(data => {
            console.log("birds_now: ", data); // Handle the data from the API
            updateBirdsNowTable(data);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
        
    } catch (error) {
        console.error('Error fetching birds_now:', error);
    }
}
async function fetchDetectionsThisWeek() {
    try {
        fetch('/api/detections_this_week/')
        .then(response => {
            console.log("fetchDetectionsThisWeek response: ", response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }).then(data => {
            console.log("fetchDetectionsThisWeek: ", data); // Handle the data from the API
            updateWeeklyBirdsTable(data);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
        
    } catch (error) {
        console.error('Error fetching detections_this_week:', error);
    }
}
async function fetchBirdDetectionsCount() {
    try {
        fetch('/api/bird_detections_count/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }).then(data => {
            console.log("fetchBirdDetectionsCount: ", data); // Handle the data from the API
            updateBirdDetectionsCountTable(data);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
        
    } catch (error) {
        console.error('Error fetching bird_detections_count:', error);
    }
}
async function fetchWavSpectrogram() {
    try {
        fetch('/api/wav_spectrogram/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }).then(data => {
            console.log("fetchWavSpectrogram: ", data); // Handle the data from the API
            if (data.length > 0) {
                updateHeatmapChart(data[0]); // Update the chart with the first index of the data
            }
        })  
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
        
    } catch (error) {
        console.error('Error fetching wav_spectrogram:', error);
    }
}
function updateWeeklyBirdsTable(birds) {
    const birdList = document.getElementById('bird-list');  // Adjust based on your HTML structure
    if (birds.length > 0) {
        birdList.innerHTML = '';  // Clear existing list

        // Calculate maxCount before deciding colors
        const maxCount = Math.max(...birds.map(bird => Math.max(...bird.slice(1))));

        birds.forEach(bird => {
            // create a tr for each common name
            const tr = document.createElement('tr');
            // add a td for each hour of the day (the 0th index is the common name)
            for (let i = 0; i <= 24; i++) {
                const tdHour = document.createElement('td');
                const count = bird[i];

                // Print "-" if count is 0, otherwise print the count
                tdHour.textContent = (i > 0 && count === 0) ? "-" : count;

                if(i > 0 && count > 0){
                    // Set background color based on the count value
                    const { backgroundColor, textColor } = getBackgroundColor(count, maxCount);
                    tdHour.style.backgroundColor = backgroundColor;
                    tdHour.style.color = textColor;
                }

                tr.appendChild(tdHour);
            }
            birdList.appendChild(tr);
        });
    }
}
function getBackgroundColor(count, maxCount) {
    // Define a custom colormap
    const colormap = [
        { threshold: 0, color: 'rgba(255, 255, 255, 1)' }, 
        { threshold: 0.6, color: 'rgba(74, 192, 0, 1)' }, 
        { threshold: 0.95, color: 'rgba(0, 94, 0, 1)' }, 
        { threshold: 1.01, color: 'rgba(155, 0, 75, 1)' } 
    ];

    const normalizedCount = Math.log1p(count) / Math.log1p(maxCount); // Logarithmic normalization
    const clampedCount = Math.min(Math.max(normalizedCount, 0), 1); // Clamp value between 0 and 1

    // Find the appropriate color based on the normalized count
    let backgroundColor;
    for (let i = 0; i < colormap.length - 1; i++) {
        if (clampedCount >= colormap[i].threshold && clampedCount < colormap[i + 1].threshold) {
            const startColor = colormap[i].color;
            const endColor = colormap[i + 1].color;
            const ratio = (clampedCount - colormap[i].threshold) / (colormap[i + 1].threshold - colormap[i].threshold);
            backgroundColor = interpolateColor(startColor, endColor, ratio);
            break;
        }
    }

    const textColor = 'black'; // Text color is black
    return { backgroundColor, textColor };
}

function interpolateColor(startColor, endColor, ratio) {
    const start = startColor.match(/\d+/g).map(Number);
    const end = endColor.match(/\d+/g).map(Number);
    const interpolated = start.map((s, i) => Math.round(s + ratio * (end[i] - s)));
    return `rgba(${interpolated.join(',')})`;
}
function updateBirdsNowTable(birds) {

    const birdList = document.getElementById('bird-list-now');  // Adjust based on your HTML structure
    if (birds.length > 0) {
    birdList.innerHTML = '';  // Clear existing list
        birds.forEach(bird => {
            const tr = document.createElement('tr');
            const tdConfidence = document.createElement('td');
            tdConfidence.textContent = Math.round(bird.confidence * 1000) / 1000;
            tr.appendChild(tdConfidence);
            const tdCommonName = document.createElement('td');
            tdCommonName.textContent = bird.common_name;
            tr.appendChild(tdCommonName);
            const tdScientificName = document.createElement('td');
            tdScientificName.textContent = bird.scientific_name;
            tr.appendChild(tdScientificName);
            birdList.appendChild(tr);
        });
        // adjust the live-detections-table-header text to include the time of the detection
        const liveDetectionsTableHeader = document.getElementById('live-detections-table-header');
        liveDetectionsTableHeader.textContent = `Detections [${birds[0].sighting_time}]`;
    }
}
function updateBirdDetectionsCountTable(birds) {
    const birdList = document.getElementById('all-time-bird-records');  
    if (birds.length > 0) {
        birdList.innerHTML = '';  // Clear existing list
        birds.forEach(bird => {
            const tr = document.createElement('tr');

            const tdCommonName = document.createElement('td');
            tdCommonName.textContent = bird.common_name;
            tr.appendChild(tdCommonName);

            const tdScientificName = document.createElement('td');
            tdScientificName.textContent = bird.scientific_name;
            tr.appendChild(tdScientificName);

            const tdCount = document.createElement('td');
            tdCount.textContent = bird.total_detections;
            tr.appendChild(tdCount);

            const tdMaxConfidence = document.createElement('td');
            tdMaxConfidence.textContent = Math.round(bird.max_confidence * 1000) / 1000; // Round to 3 decimal places
            // Create a speaker icon link
            const speakerLink = document.createElement('a');
            speakerLink.href = '#'; // Set the link to the desired URL or function
            const speakerIcon = document.createElement('img');
            speakerIcon.src = '/static/img/Speaker_Icon.png'; 
            speakerIcon.alt = 'Play best recording';
            speakerIcon.style.width = '20px'; // Set the desired width
            speakerIcon.style.height = '20px'; // Set the desired height
            speakerLink.appendChild(speakerIcon);
            speakerLink.style.marginLeft = '5px'; // Add spacing between text and icon
            tdMaxConfidence.appendChild(speakerLink);
            tr.appendChild(tdMaxConfidence);

            birdList.appendChild(tr);
        });
    }
}

// function generateSpectrogram() {
//     const spectrogram = document.getElementById('spectrogram');
//     spectrogram.innerHTML = '';
//     // generate a spectrogram of the last 10 seconds of audio
//     const audio = document.getElementById('audio');
//     const audioContext = new AudioContext();
// }

const customColorScale = [
    [0.0, 'rgb(26, 0, 33)'],   
    [0.05, 'rgb(0, 122, 156)'], 
    [0.15, 'rgb(0, 171, 219)'], 
    [0.3, 'rgb(0, 255, 76)'],
    [0.7, 'rgb(238, 255, 0)'],
    [1.0, 'rgb(255, 0, 0)'],
];
// Function to update the heatmap chart with new data
function updateHeatmapChart(spectrogramData) {
    // Assuming spectrogramData contains frequencies, times, and spectrogram arrays
    let { frequencies, times, spectrogram } = spectrogramData;

    // Downsample the data
    // const downsampleFactor = 10; // Adjust this factor as needed
    // frequencies = downsampleData(frequencies, downsampleFactor);
    // times = downsampleData(times, downsampleFactor);
    // spectrogram = downsample2DArray(spectrogram, downsampleFactor);

    const data = [{
        z: spectrogram,
        x: times,
        y: frequencies,
        type: 'heatmap',
        colorscale: customColorScale // Use the custom color scale
    }];

    const layout = {
        title: {
            text: 'Spectrogram',
        },
        xaxis: {
            title: {
              text: 'Time (s)',
            },
          },
          yaxis: {
            title: {
              text: 'Frequency (Hz)',
            }
          }
    };

    Plotly.newPlot('heatmap', data, layout);
}

function downsampleData(data, factor) {
    const downsampled = [];
    for (let i = 0; i < data.length; i += factor) {
        const chunk = data.slice(i, i + factor);
        const average = chunk.reduce((sum, value) => sum + value, 0) / chunk.length;
        downsampled.push(average);
    }
    return downsampled;
}
function downsample2DArray(array, factor) {
    return array.map(row => downsampleData(row, factor));
}

function updateObservationHistoryDays() {
    fetch('/api/observation_history_days/')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    }).then(data => {
        console.log("observation_history_days: ", data);
        const observationHistoryDays = data.history_days;
        const observationHistoryDaysHeader = document.getElementById('bird-observations-header');
        observationHistoryDaysHeader.textContent = `Bird Observations (last ${observationHistoryDays} days)`;
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });
}   

// Call fetchBirds and initializeHeatmapChart when the window loads
window.onload = function() {
    updateObservationHistoryDays();
    fetchBirdsNow();
    fetchDetectionsThisWeek();
    // fetchBirdDetectionsCount();
    fetchWavSpectrogram();  // Fetch and plot the spectrogram
};


function updateAll() {
    fetchBirdsNow();
    fetchDetectionsThisWeek();
    fetchWavSpectrogram();  // Fetch and plot the spectrogram
}

