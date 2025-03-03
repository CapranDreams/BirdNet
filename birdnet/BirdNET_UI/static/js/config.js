function loadBirdsConfig() {
    fetch('/api/birds_config/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('confidence_threshold').value = data.confidence_threshold || '';
            document.getElementById('history_days').value = data.history_days || '';
            document.getElementById('max_frequency').value = data.max_frequency || '';
            document.getElementById('latitude').value = data.latitude || '';
            document.getElementById('longitude').value = data.longitude || '';
            document.getElementById('state').value = data.state || '';
            document.getElementById('subregion_code').value = data.subregion_code || '';
            document.getElementById('confidence_threshold_for_add_to_db').value = data.confidence_threshold_for_add_to_db || '';
        })
        .catch(error => {
            console.error('Error loading birds config:', error);
        });
}

function saveBirdsConfig() {
    const configData = {
        confidence_threshold: document.getElementById('confidence_threshold').value,
        history_days: document.getElementById('history_days').value,
        max_frequency: document.getElementById('max_frequency').value,
        latitude: document.getElementById('latitude').value,
        longitude: document.getElementById('longitude').value,
        state: document.getElementById('state').value,
        subregion_code: document.getElementById('subregion_code').value,
        confidence_threshold_for_add_to_db: document.getElementById('confidence_threshold_for_add_to_db').value
    };

    fetch('/api/update_birds_config/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(configData),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // alert('Bird detection settings saved successfully!');
            // Redirect to the home page after successful save
            window.location.href = '/';
        } else {
            alert('Error saving settings: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving settings: ' + error);
    });
}


document.addEventListener('DOMContentLoaded', function() {
    loadBirdsConfig();

    document.getElementById('save-settings-button').addEventListener('click', function(e) {
        e.preventDefault(); // Prevent default form submission
        saveBirdsConfig();
    });
});