// Vehicle Selector JavaScript - Hybrid Browse All / My Vehicles

let currentMode = 'browse'; // 'browse' or 'my'
let selectedVehicle = null;
let myVehicles = [];

// Initialize vehicle selector on page load
document.addEventListener('DOMContentLoaded', function() {
    loadMyVehicles();
    initializeBrowseMode();
});

// Switch between browse and my vehicles modes
function switchVehicleMode(mode) {
    currentMode = mode;
    
    // Update tabs
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (mode === 'browse') {
        document.getElementById('browseAllTab').classList.add('active');
        document.getElementById('browseAllMode').classList.add('active');
        document.getElementById('myVehiclesMode').classList.remove('active');
    } else {
        document.getElementById('myVehiclesTab').classList.add('active');
        document.getElementById('myVehiclesMode').classList.add('active');
        document.getElementById('browseAllMode').classList.remove('active');
    }
}

// Load user's saved vehicles
async function loadMyVehicles() {
    try {
        const response = await fetch('/api/vehicles/my-vehicles');
        myVehicles = await response.json();
        
        const listContainer = document.getElementById('myVehiclesList');
        
        if (myVehicles.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <p>No vehicles saved yet.</p>
                    <p>Click "Add Vehicle" to get started.</p>
                </div>
            `;
        } else {
            listContainer.innerHTML = myVehicles.map(vehicle => `
                <div class="vehicle-profile-item ${selectedVehicle?.vin === vehicle.vin ? 'selected' : ''}" 
                     onclick="selectVehicle('${vehicle.vin}')"
                     data-vin="${vehicle.vin}">
                    <div class="vehicle-profile-main">
                        <div class="vehicle-profile-title">
                            ${vehicle.make} ${vehicle.model} ${vehicle.submodel}
                        </div>
                        <div class="vehicle-profile-details">
                            ${vehicle.year} • ${vehicle.body} • ${vehicle.plate}
                        </div>
                        <div class="vehicle-profile-vin">
                            VIN: ${vehicle.vin}
                        </div>
                    </div>
                    <div class="vehicle-profile-actions">
                        <button class="btn-icon" onclick="editVehicle(event, '${vehicle.vin}')" title="Edit">
                            <i class="icon-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="deleteVehicle(event, '${vehicle.vin}')" title="Delete">
                            <i class="icon-delete"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load vehicles:', error);
        document.getElementById('myVehiclesList').innerHTML = `
            <div class="error-state">
                <p>Failed to load vehicles.</p>
                <button class="btn-primary" onclick="loadMyVehicles()">Retry</button>
            </div>
        `;
    }
}

// Initialize browse mode with hierarchy
function initializeBrowseMode() {
    // Load manufacturers
    loadManufacturers();
    
    // Set up cascade listeners
    document.getElementById('manufacturerSelect').addEventListener('change', onManufacturerChange);
    document.getElementById('modelSelect').addEventListener('change', onModelChange);
    document.getElementById('generationSelect').addEventListener('change', onGenerationChange);
    document.getElementById('variantSelect').addEventListener('change', onVariantChange);
}

// Load manufacturers for browse mode
async function loadManufacturers() {
    try {
        const response = await fetch('/api/vehicles/manufacturers');
        const manufacturers = await response.json();
        
        const select = document.getElementById('manufacturerSelect');
        manufacturers.forEach(m => {
            const option = document.createElement('option');
            option.value = m;
            option.textContent = m;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load manufacturers:', error);
    }
}

// Handle manufacturer selection
async function onManufacturerChange(event) {
    const manufacturer = event.target.value;
    const modelSelect = document.getElementById('modelSelect');
    
    // Reset downstream selects
    modelSelect.innerHTML = '<option value="">Select manufacturer first</option>';
    modelSelect.disabled = !manufacturer;
    document.getElementById('generationSelect').disabled = true;
    document.getElementById('variantSelect').disabled = true;
    
    if (manufacturer) {
        try {
            const response = await fetch(`/api/vehicles/models?manufacturer=${manufacturer}`);
            const models = await response.json();
            
            models.forEach(m => {
                const option = document.createElement('option');
                option.value = m;
                option.textContent = m;
                modelSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }
}

// Handle model selection
async function onModelChange(event) {
    const manufacturer = document.getElementById('manufacturerSelect').value;
    const model = event.target.value;
    const generationSelect = document.getElementById('generationSelect');
    
    // Reset downstream selects
    generationSelect.innerHTML = '<option value="">Select model first</option>';
    generationSelect.disabled = !model;
    document.getElementById('variantSelect').disabled = true;
    
    if (model) {
        try {
            const response = await fetch(`/api/vehicles/generations?manufacturer=${manufacturer}&model=${model}`);
            const generations = await response.json();
            
            generations.forEach(g => {
                const option = document.createElement('option');
                option.value = g;
                option.textContent = g;
                generationSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load generations:', error);
        }
    }
}

// Handle generation selection
async function onGenerationChange(event) {
    const manufacturer = document.getElementById('manufacturerSelect').value;
    const model = document.getElementById('modelSelect').value;
    const generation = event.target.value;
    const variantSelect = document.getElementById('variantSelect');
    
    // Reset variant select
    variantSelect.innerHTML = '<option value="">Select generation first</option>';
    variantSelect.disabled = !generation;
    
    if (generation) {
        try {
            const response = await fetch(`/api/vehicles/variants?manufacturer=${manufacturer}&model=${model}&generation=${generation}`);
            const variants = await response.json();
            
            variants.forEach(v => {
                const option = document.createElement('option');
                option.value = v.id;
                option.textContent = v.name;
                variantSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load variants:', error);
        }
    }
}

// Handle variant selection
function onVariantChange(event) {
    const variantId = event.target.value;
    
    if (variantId) {
        // Find the variant data
        const manufacturer = document.getElementById('manufacturerSelect').value;
        const model = document.getElementById('modelSelect').value;
        const generation = document.getElementById('generationSelect').value;
        
        // Load variant details and select vehicle
        loadVariantDetails(variantId);
    }
}

// Load variant details
async function loadVariantDetails(variantId) {
    try {
        const response = await fetch(`/api/vehicles/variant/${variantId}`);
        const variant = await response.json();
        
        // Create a temporary vehicle object
        selectedVehicle = {
            id: variantId,
            make: variant.manufacturer,
            model: variant.model,
            submodel: variant.name,
            year: variant.year_range[0], // Use first year
            body: variant.body_type || 'Unknown',
            vin: null, // Generic variant has no VIN
            isTemplate: true
        };
        
        updateSelectedVehicleDisplay();
        notifyVehicleChanged();
    } catch (error) {
        console.error('Failed to load variant details:', error);
    }
}

// Select a vehicle from My Vehicles
function selectVehicle(vin) {
    const vehicle = myVehicles.find(v => v.vin === vin);
    if (vehicle) {
        selectedVehicle = vehicle;
        selectedVehicle.isTemplate = false;
        
        // Update UI
        document.querySelectorAll('.vehicle-profile-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-vin="${vin}"]`).classList.add('selected');
        
        updateSelectedVehicleDisplay();
        notifyVehicleChanged();
    }
}

// Update the selected vehicle display
function updateSelectedVehicleDisplay() {
    const display = document.getElementById('selectedVehicleDisplay');
    const nameElement = document.getElementById('selectedVehicleName');
    
    if (selectedVehicle) {
        nameElement.textContent = selectedVehicle.get_display_name || 
            `${selectedVehicle.make} ${selectedVehicle.model} ${selectedVehicle.submodel} (${selectedVehicle.year})`;
        display.style.display = 'flex';
    } else {
        display.style.display = 'none';
    }
}

// Notify other components that vehicle changed
function notifyVehicleChanged() {
    // Dispatch custom event
    const event = new CustomEvent('vehicleChanged', {
        detail: selectedVehicle
    });
    document.dispatchEvent(event);
    
    // Update app state
    if (window.appState) {
        window.appState.selectedVehicle = selectedVehicle;
    }
}

// Show add vehicle dialog
function showAddVehicleDialog() {
    document.getElementById('addVehicleModal').classList.add('active');
}

// Close add vehicle dialog
function closeAddVehicleDialog() {
    document.getElementById('addVehicleModal').classList.remove('active');
    clearVehicleForm();
}

// Clear vehicle form
function clearVehicleForm() {
    document.getElementById('vinInput').value = '';
    document.getElementById('plateInput').value = '';
    document.getElementById('engineNumberInput').value = '';
    document.getElementById('yearInput').value = '';
    document.getElementById('makeInput').value = '';
    document.getElementById('modelInput').value = '';
    document.getElementById('submodelInput').value = '';
    document.getElementById('bodyInput').value = '';
    document.getElementById('fuelInput').value = '';
    document.getElementById('colourInput').value = '';
}

// Save vehicle profile
async function saveVehicleProfile() {
    const vehicleData = {
        vin: document.getElementById('vinInput').value.toUpperCase(),
        plate: document.getElementById('plateInput').value,
        engine_number: document.getElementById('engineNumberInput').value,
        year: parseInt(document.getElementById('yearInput').value),
        make: document.getElementById('makeInput').value,
        model: document.getElementById('modelInput').value,
        submodel: document.getElementById('submodelInput').value,
        body: document.getElementById('bodyInput').value,
        fuel_type: document.getElementById('fuelInput').value,
        colour: document.getElementById('colourInput').value
    };
    
    // Basic validation
    if (!vehicleData.vin || vehicleData.vin.length !== 17) {
        alert('Please enter a valid 17-character VIN');
        return;
    }
    
    if (!vehicleData.make || !vehicleData.model) {
        alert('Please enter make and model');
        return;
    }
    
    try {
        const response = await fetch('/api/vehicles/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(vehicleData)
        });
        
        if (response.ok) {
            closeAddVehicleDialog();
            loadMyVehicles();
            
            // Auto-select the new vehicle
            selectVehicle(vehicleData.vin);
            
            // Switch to My Vehicles tab
            switchVehicleMode('my');
        } else {
            const error = await response.json();
            alert('Failed to save vehicle: ' + error.message);
        }
    } catch (error) {
        console.error('Failed to save vehicle:', error);
        alert('Failed to save vehicle. Please try again.');
    }
}

// Edit vehicle (placeholder)
function editVehicle(event, vin) {
    event.stopPropagation();
    console.log('Edit vehicle:', vin);
    // TODO: Implement edit functionality
}

// Delete vehicle
async function deleteVehicle(event, vin) {
    event.stopPropagation();
    
    if (confirm('Are you sure you want to delete this vehicle?')) {
        try {
            const response = await fetch(`/api/vehicles/profile/${vin}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                // Remove from UI
                const element = document.querySelector(`[data-vin="${vin}"]`);
                element.remove();
                
                // Remove from array
                myVehicles = myVehicles.filter(v => v.vin !== vin);
                
                // Clear selection if this was selected
                if (selectedVehicle?.vin === vin) {
                    selectedVehicle = null;
                    updateSelectedVehicleDisplay();
                }
            } else {
                alert('Failed to delete vehicle');
            }
        } catch (error) {
            console.error('Failed to delete vehicle:', error);
            alert('Failed to delete vehicle. Please try again.');
        }
    }
}
