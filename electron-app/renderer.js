// VersaTuner Electron Renderer Process

// Vehicle Constants Manager Class
class VehicleConstantsManager {
    constructor() {
        this.currentVehicle = null;
        this.currentConstants = null;
        this.presets = [];
        this.hierarchy = {};
        this.modifiedFields = new Set();
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadHierarchy();
        this.loadVehicles();
        this.initTabs();
    }

    initTabs() {
        // Tab switching
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;

                // Update active states
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));

                button.classList.add('active');
                document.getElementById(`${tabName}-tab`).classList.add('active');
            });
        });
    }

    bindEvents() {
        // Hierarchical selection
        document.getElementById('manufacturerSelector').addEventListener('change', (e) => {
            this.onManufacturerChange(e.target.value);
        });

        document.getElementById('platformSelector').addEventListener('change', (e) => {
            this.onPlatformChange(e.target.value);
        });

        document.getElementById('modelSelector').addEventListener('change', (e) => {
            this.onModelChange(e.target.value);
        });

        document.getElementById('generationSelector').addEventListener('change', (e) => {
            this.onGenerationChange(e.target.value);
        });

        document.getElementById('variantSelector').addEventListener('change', (e) => {
            this.onVariantChange(e.target.value);
        });

        document.getElementById('transmissionSelector').addEventListener('change', (e) => {
            this.onTransmissionChange(e.target.value);
        });

        // Import functionality
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const selectFileBtn = document.getElementById('selectFileBtn');

        uploadArea.addEventListener('click', () => fileInput.click());
        selectFileBtn.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        document.getElementById('confirmImportBtn').addEventListener('click', () => {
            this.confirmImport();
        });

        document.getElementById('cancelImportBtn').addEventListener('click', () => {
            this.cancelImport();
        });

        // Original buttons
        document.getElementById('restoreDefaultsBtn').addEventListener('click', () => {
            this.restoreDefaults();
        });

        document.getElementById('saveConstantsBtn').addEventListener('click', () => {
            this.saveConstants();
        });

        document.getElementById('recalculateDynoBtn').addEventListener('click', () => {
            this.recalculateDyno();
        });

        // Track modifications
        const inputs = document.querySelectorAll('.neon-input:not([readonly])');
        inputs.forEach(input => {
            input.addEventListener('input', (e) => {
                this.onFieldChange(e.target);
            });
        });
    }

    async loadHierarchy() {
        try {
            this.hierarchy = await window.api.getPresetHierarchy();
            const selector = document.getElementById('manufacturerSelector');

            selector.innerHTML = '<option value="">Select Manufacturer...</option>';
            Object.keys(this.hierarchy).forEach(manufacturer => {
                const option = document.createElement('option');
                option.value = manufacturer;
                option.textContent = manufacturer;
                selector.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load hierarchy:', error);
        }
    }

    onManufacturerChange(manufacturer) {
        const platformSelector = document.getElementById('platformSelector');
        const modelSelector = document.getElementById('modelSelector');

        // Reset downstream selectors
        platformSelector.innerHTML = '<option value="">Select Platform...</option>';
        modelSelector.innerHTML = '<option value="">Select Model...</option>';
        document.getElementById('generationSelector').innerHTML = '<option value="">Select Generation...</option>';
        document.getElementById('variantSelector').innerHTML = '<option value="">Select Variant...</option>';
        document.getElementById('transmissionSelector').innerHTML = '<option value="">Select Transmission...</option>';

        if (!manufacturer) {
            platformSelector.disabled = true;
            modelSelector.disabled = true;
            document.getElementById('generationSelector').disabled = true;
            document.getElementById('variantSelector').disabled = true;
            document.getElementById('transmissionSelector').disabled = true;
            return;
        }

        platformSelector.disabled = false;

        // Populate platforms
        Object.keys(this.hierarchy[manufacturer]).forEach(platform => {
            const option = document.createElement('option');
            option.value = platform;
            option.textContent = platform;
            platformSelector.appendChild(option);
        });
    }

    onPlatformChange(platform) {
        const manufacturer = document.getElementById('manufacturerSelector').value;
        const modelSelector = document.getElementById('modelSelector');

        modelSelector.innerHTML = '<option value="">Select Model...</option>';
        document.getElementById('generationSelector').innerHTML = '<option value="">Select Generation...</option>';
        document.getElementById('variantSelector').innerHTML = '<option value="">Select Variant...</option>';
        document.getElementById('transmissionSelector').innerHTML = '<option value="">Select Transmission...</option>';

        if (!platform) {
            modelSelector.disabled = true;
            document.getElementById('generationSelector').disabled = true;
            document.getElementById('variantSelector').disabled = true;
            document.getElementById('transmissionSelector').disabled = true;
            return;
        }

        modelSelector.disabled = false;

        // Populate models
        Object.keys(this.hierarchy[manufacturer][platform]).forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelector.appendChild(option);
        });
    }

    onModelChange(model) {
        const manufacturer = document.getElementById('manufacturerSelector').value;
        const platform = document.getElementById('platformSelector').value;
        const bodySelector = document.getElementById('bodySelector');

        bodySelector.innerHTML = '<option value="">Select Body...</option>';
        document.getElementById('generationSelector').innerHTML = '<option value="">Select Generation...</option>';
        document.getElementById('variantSelector').innerHTML = '<option value="">Select Variant...</option>';
        document.getElementById('transmissionSelector').innerHTML = '<option value="">Select Transmission...</option>';

        if (!model) {
            bodySelector.disabled = true;
            document.getElementById('generationSelector').disabled = true;
            document.getElementById('variantSelector').disabled = true;
            document.getElementById('transmissionSelector').disabled = true;
            return;
        }

        bodySelector.disabled = false;

        // Get unique bodies
        const variants = this.hierarchy[manufacturer][platform][model];
        const bodies = [...new Set(variants.map(v => v.body).filter(b => b))];

        bodies.forEach(body => {
            const option = document.createElement('option');
            option.value = body;
            option.textContent = body;
            bodySelector.appendChild(option);
        });
    }

    onBodyChange(body) {
        const manufacturer = document.getElementById('manufacturerSelector').value;
        const platform = document.getElementById('platformSelector').value;
        const model = document.getElementById('modelSelector').value;
        const generationSelector = document.getElementById('generationSelector');

        generationSelector.innerHTML = '<option value="">Select Generation...</option>';
        document.getElementById('variantSelector').innerHTML = '<option value="">Select Variant...</option>';
        document.getElementById('transmissionSelector').innerHTML = '<option value="">Select Transmission...</option>';

        if (!body) {
            generationSelector.disabled = true;
            document.getElementById('variantSelector').disabled = true;
            document.getElementById('transmissionSelector').disabled = true;
            return;
        }

        generationSelector.disabled = false;

        // Get unique generations for this body
        const variants = this.hierarchy[manufacturer][platform][model];
        const bodyVariants = variants.filter(v => v.body === body);
        const generations = [...new Set(bodyVariants.map(v => v.generation).filter(g => g))];

        generations.forEach(generation => {
            const option = document.createElement('option');
            option.value = generation;
            option.textContent = generation;
            generationSelector.appendChild(option);
        });
    }

    onGenerationChange(generation) {
        const manufacturer = document.getElementById('manufacturerSelector').value;
        const platform = document.getElementById('platformSelector').value;
        const model = document.getElementById('modelSelector').value;
        const body = document.getElementById('bodySelector').value;
        const variantSelector = document.getElementById('variantSelector');

        variantSelector.innerHTML = '<option value="">Select Variant...</option>';
        document.getElementById('transmissionSelector').innerHTML = '<option value="">Select Transmission...</option>';

        if (!generation) {
            variantSelector.disabled = true;
            document.getElementById('transmissionSelector').disabled = true;
            return;
        }

        variantSelector.disabled = false;

        // Get unique variants for this body and generation
        const variants = this.hierarchy[manufacturer][platform][model];
        const filteredVariants = variants.filter(v => v.body === body && v.generation === generation);
        const uniqueVariants = [...new Set(filteredVariants.map(v => v.variant).filter(v => v))];

        uniqueVariants.forEach(variant => {
            const option = document.createElement('option');
            option.value = variant;
            option.textContent = variant;
            variantSelector.appendChild(option);
        });
    }

    onVariantChange(variant) {
        const manufacturer = document.getElementById('manufacturerSelector').value;
        const platform = document.getElementById('platformSelector').value;
        const model = document.getElementById('modelSelector').value;
        const body = document.getElementById('bodySelector').value;
        const generation = document.getElementById('generationSelector').value;
        const transmissionSelector = document.getElementById('transmissionSelector');

        transmissionSelector.innerHTML = '<option value="">Select Transmission...</option>';

        if (!variant) {
            transmissionSelector.disabled = true;
            return;
        }

        transmissionSelector.disabled = false;

        // Get available transmissions for this specific variant
        const variants = this.hierarchy[manufacturer][platform][model];
        const matchingVariants = variants.filter(v =>
            v.body === body &&
            v.generation === generation &&
            v.variant === variant
        );

        const transmissions = [...new Set(matchingVariants.map(v => v.transmission_type).filter(t => t))];

        transmissions.forEach(transmission => {
            const option = document.createElement('option');
            option.value = transmission;
            option.textContent = transmission;
            transmissionSelector.appendChild(option);
        });
    }

    onTransmissionChange(transmission) {
        const manufacturer = document.getElementById('manufacturerSelector').value;
        const platform = document.getElementById('platformSelector').value;
        const model = document.getElementById('modelSelector').value;
        const body = document.getElementById('bodySelector').value;
        const generation = document.getElementById('generationSelector').value;
        const variant = document.getElementById('variantSelector').value;

        if (!transmission) {
            return;
        }

        // Find the matching preset
        const variants = this.hierarchy[manufacturer][platform][model];
        const matchingPreset = variants.find(v =>
            v.body === body &&
            v.generation === generation &&
            v.variant === variant &&
            v.transmission_type === transmission
        );

        if (matchingPreset) {
            this.loadPresetConstants(matchingPreset);
            this.updateVehicleCapabilities(manufacturer, model, generation, body, transmission);
        }
    }

    async updateVehicleCapabilities(manufacturer, model, generation, body, transmission) {
        try {
            // Fetch vehicle capabilities from API
            const response = await fetch(`/api/vehicle-capabilities`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    manufacturer,
                    model,
                    generation,
                    body,
                    transmission
                })
            });

            if (response.ok) {
                const capabilities = await response.json();
                this.displayVehicleCapabilities(capabilities);
                this.displayDiagnosticsCapabilities(capabilities);
            } else {
                console.error('Failed to fetch vehicle capabilities');
            }
        } catch (error) {
            console.error('Error fetching vehicle capabilities:', error);
        }
    }

    displayDiagnosticsCapabilities(capabilities) {
        const panel = document.getElementById('diagnosticsCapabilityPanel');

        if (!capabilities || capabilities.status === 'UNKNOWN') {
            panel.style.display = 'none';
            return;
        }

        panel.style.display = 'block';

        // Update vehicle info
        const vehicleInfo = `${capabilities.manufacturer} ${capabilities.model}`;
        document.getElementById('capabilityVehicleInfo').textContent = vehicleInfo;
        document.getElementById('capabilityProtocolInfo').textContent = capabilities.primary_protocol || 'Unknown';

        // Build capability matrix
        const matrixBody = document.getElementById('capabilityMatrixBody');
        matrixBody.innerHTML = '';

        const modules = [
            { key: 'ENGINE', name: 'Engine ECU' },
            { key: 'TRANSMISSION', name: 'Transmission' },
            { key: 'TCM', name: 'TCM (DSG/TCT)' },
            { key: 'ABS', name: 'ABS' },
            { key: 'SRS', name: 'SRS/Airbag' },
            { key: 'BCM', name: 'Body Control' },
            { key: 'CLUSTER', name: 'Instrument Cluster' }
        ];

        const services = [
            'READ_DTCS',
            'CLEAR_DTCS',
            'LIVE_DATA',
            'FREEZE_FRAME',
            'READINESS',
            'CODING',
            'ADAPTATION',
            'SERVICE_FUNCTIONS'
        ];

        const unsupportedFeatures = [];

        modules.forEach(module => {
            const row = document.createElement('tr');

            // Module name cell
            const moduleCell = document.createElement('td');
            moduleCell.className = 'module-name';
            moduleCell.textContent = module.name;
            row.appendChild(moduleCell);

            // Service status cells
            let hasAnySupported = false;
            services.forEach(service => {
                const cell = document.createElement('td');
                const status = this.getServiceStatus(capabilities, module.key, service);

                const statusSpan = document.createElement('span');
                statusSpan.className = `service-status ${status.class}`;
                statusSpan.textContent = status.text;

                cell.appendChild(statusSpan);
                row.appendChild(cell);

                if (status.class === 'supported') {
                    hasAnySupported = true;
                }
            });

            // Add click handler to show details
            row.addEventListener('click', () => {
                this.showModuleDetails(module.key, capabilities);
            });

            // Add to unsupported list if no services supported
            if (!hasAnySupported) {
                unsupportedFeatures.push(`${module.name}: No services supported`);
            }

            matrixBody.appendChild(row);
        });

        // Show unsupported features notice if any
        if (unsupportedFeatures.length > 0) {
            const notice = document.getElementById('unsupportedNotice');
            const list = document.getElementById('unsupportedFeaturesList');
            list.innerHTML = '';

            unsupportedFeatures.forEach(feature => {
                const li = document.createElement('li');
                li.textContent = feature;
                list.appendChild(li);
            });

            notice.style.display = 'block';
        } else {
            document.getElementById('unsupportedNotice').style.display = 'none';
        }
    }

    getServiceStatus(capabilities, module, service) {
        // Check module capabilities
        if (capabilities.modules && capabilities.modules[module]) {
            const moduleCap = capabilities.modules[module];
            if (moduleCap.services && moduleCap.services[service]) {
                const serviceCap = moduleCap.services[service];
                return {
                    class: serviceCap.status.toLowerCase(),
                    text: serviceCap.status
                };
            }
        }

        // Fallback to legacy service capabilities
        if (capabilities.services && capabilities.services[service]) {
            const serviceCap = capabilities.services[service];
            return {
                class: serviceCap.supported ? 'supported' : 'not-supported',
                text: serviceCap.supported ? 'SUPPORTED' : 'NOT_SUPPORTED'
            };
        }

        return {
            class: 'unknown',
            text: 'UNKNOWN'
        };
    }

    showModuleDetails(module, capabilities) {
        const panel = document.getElementById('moduleDetailsPanel');
        const moduleCap = capabilities.modules && capabilities.modules[module];

        if (!moduleCap) {
            panel.style.display = 'none';
            return;
        }

        // Update details
        document.getElementById('detailModuleName').textContent = module;
        document.getElementById('detailModuleStatus').textContent = moduleCap.status || 'UNKNOWN';
        document.getElementById('detailModuleStatus').className = `status-badge ${moduleCap.status ? moduleCap.status.toLowerCase() : 'unknown'}`;
        document.getElementById('detailModuleProtocol').textContent = moduleCap.protocol_info || 'Standard';
        document.getElementById('detailModuleNotes').textContent = moduleCap.reason || moduleCap.notes || 'No additional information';

        panel.style.display = 'block';
    }

    // Admin Override Management
    initAdminOverrides() {
        // Override scope change handler
        const scopeSelect = document.getElementById('overrideScope');
        scopeSelect.addEventListener('change', () => {
            this.updateOverrideControls();
        });

        // Activate override button
        const activateBtn = document.getElementById('activateOverrideBtn');
        activateBtn.addEventListener('click', () => {
            this.showOverrideActivationModal();
        });

        // Revoke override button
        const revokeBtn = document.getElementById('revokeOverrideBtn');
        revokeBtn.addEventListener('click', () => {
            this.revokeOverride();
        });

        // Confirmation input handler
        const confirmInput = document.getElementById('overrideConfirmation');
        confirmInput.addEventListener('input', () => {
            const confirmBtn = document.getElementById('confirmOverrideBtn');
            confirmBtn.disabled = confirmInput.value !== 'OVERRIDE';
        });

        // Confirm override button
        const confirmBtn = document.getElementById('confirmOverrideBtn');
        confirmBtn.addEventListener('click', () => {
            this.activateOverride();
        });

        // View audit log button
        const auditBtn = document.getElementById('viewAuditLogBtn');
        auditBtn.addEventListener('click', () => {
            this.showAuditLog();
        });

        // Check for admin role and show panel
        this.checkAdminRole();
    }

    updateOverrideControls() {
        const scope = document.getElementById('overrideScope').value;
        const moduleGroup = document.getElementById('moduleGroup');
        const actionGroup = document.getElementById('actionGroup');
        const durationGroup = document.getElementById('durationGroup');

        // Hide all optional groups
        moduleGroup.style.display = 'none';
        actionGroup.style.display = 'none';
        durationGroup.style.display = 'none';

        // Show relevant groups based on scope
        if (scope === 'MODULE' || scope === 'ACTION') {
            moduleGroup.style.display = 'block';
        }

        if (scope === 'ACTION') {
            actionGroup.style.display = 'block';
        }

        if (scope === 'MODULE') {
            durationGroup.style.display = 'block';
        }

        // Update activate button state
        this.updateActivateButtonState();
    }

    updateActivateButtonState() {
        const scope = document.getElementById('overrideScope').value;
        const reason = document.getElementById('overrideReason').value.trim();
        const activateBtn = document.getElementById('activateOverrideBtn');

        let canActivate = scope && reason;

        if (scope === 'MODULE' || scope === 'ACTION') {
            const module = document.getElementById('overrideModule').value;
            canActivate = canActivate && module;
        }

        if (scope === 'ACTION') {
            const action = document.getElementById('overrideAction').value;
            canActivate = canActivate && action;
        }

        activateBtn.disabled = !canActivate;
    }

    async checkAdminRole() {
        try {
            const response = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const profile = await response.json();
                if (profile.role === 'admin') {
                    document.getElementById('adminOverridePanel').style.display = 'block';
                    this.checkActiveOverride();
                }
            }
        } catch (error) {
            console.error('Failed to check admin role:', error);
        }
    }

    async checkActiveOverride() {
        try {
            const response = await fetch('/api/admin/overrides/active', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.overrides && data.overrides.length > 0) {
                    this.showActiveOverride(data.overrides[0]);
                } else {
                    this.showOverrideControls();
                }
            }
        } catch (error) {
            console.error('Failed to check active override:', error);
        }
    }

    showActiveOverride(override) {
        const controls = document.getElementById('overrideControls');
        const display = document.getElementById('activeOverrideDisplay');
        const revokeBtn = document.getElementById('revokeOverrideBtn');
        const indicator = document.querySelector('.override-indicator');

        // Hide controls, show active display
        controls.style.display = 'none';
        display.style.display = 'block';
        revokeBtn.style.display = 'inline-block';

        // Update indicator
        indicator.classList.remove('inactive');
        indicator.classList.add('active');

        // Update display details
        document.getElementById('activeScope').textContent = override.scope;
        document.getElementById('activeModule').textContent = override.module || 'N/A';
        document.getElementById('activeAction').textContent = override.action || 'N/A';
        document.getElementById('activeReason').textContent = override.reason;

        const expiresGroup = document.getElementById('activeExpiresGroup');
        if (override.expires_at) {
            expiresGroup.style.display = 'flex';
            const expires = new Date(override.expires_at);
            document.getElementById('activeExpires').textContent = expires.toLocaleString();

            // Start countdown
            this.startExpirationCountdown(expires);
        } else {
            expiresGroup.style.display = 'none';
        }
    }

    showOverrideControls() {
        const controls = document.getElementById('overrideControls');
        const display = document.getElementById('activeOverrideDisplay');
        const revokeBtn = document.getElementById('revokeOverrideBtn');
        const indicator = document.querySelector('.override-indicator');

        // Show controls, hide active display
        controls.style.display = 'block';
        display.style.display = 'none';
        revokeBtn.style.display = 'none';

        // Update indicator
        indicator.classList.remove('active');
        indicator.classList.add('inactive');
    }

    startExpirationCountdown(expiresAt) {
        const updateCountdown = () => {
            const now = new Date();
            const diff = expiresAt - now;

            if (diff <= 0) {
                this.checkActiveOverride(); // Refresh when expired
                return;
            }

            const minutes = Math.floor(diff / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);

            const expiresElement = document.getElementById('activeExpires');
            if (expiresElement) {
                expiresElement.textContent = `${minutes}m ${seconds}s`;
            }

            setTimeout(updateCountdown, 1000);
        };

        updateCountdown();
    }

    showOverrideActivationModal() {
        const scope = document.getElementById('overrideScope').value;
        const module = document.getElementById('overrideModule').value;
        const action = document.getElementById('overrideAction').value;
        const duration = document.getElementById('overrideDuration').value;
        const reason = document.getElementById('overrideReason').value;

        // Update confirmation details
        document.getElementById('confirmScope').textContent = scope;
        document.getElementById('confirmModule').textContent = module || 'N/A';
        document.getElementById('confirmAction').textContent = action || 'N/A';
        document.getElementById('confirmDuration').textContent =
            scope === 'MODULE' ? `${duration} minutes` : 'N/A';
        document.getElementById('confirmReason').textContent = reason;

        // Reset confirmation input
        document.getElementById('overrideConfirmation').value = '';
        document.getElementById('confirmOverrideBtn').disabled = true;

        // Show modal
        document.getElementById('overrideActivationModal').style.display = 'flex';
    }

    async activateOverride() {
        const scope = document.getElementById('overrideScope').value;
        const module = document.getElementById('overrideModule').value;
        const action = document.getElementById('overrideAction').value;
        const duration = parseInt(document.getElementById('overrideDuration').value);
        const reason = document.getElementById('overrideReason').value;

        try {
            const response = await fetch('/api/admin/overrides/activate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    scope: scope,
                    module: module,
                    action: action,
                    duration_minutes: duration,
                    reason: reason,
                    session_id: this.getSessionId(),
                    vehicle_profile: this.getCurrentVehicleProfile()
                })
            });

            if (response.ok) {
                this.closeOverrideModal();
                this.checkActiveOverride();
                this.showNotification('Override activated', 'warning');
            } else {
                const error = await response.json();
                this.showNotification(`Failed to activate override: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Failed to activate override:', error);
            this.showNotification('Failed to activate override', 'error');
        }
    }

    async revokeOverride() {
        try {
            const response = await fetch('/api/admin/overrides/revoke', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    session_id: this.getSessionId()
                })
            });

            if (response.ok) {
                this.showOverrideControls();
                this.showNotification('Override revoked', 'success');
            } else {
                const error = await response.json();
                this.showNotification(`Failed to revoke override: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Failed to revoke override:', error);
            this.showNotification('Failed to revoke override', 'error');
        }
    }

    closeOverrideModal() {
        document.getElementById('overrideActivationModal').style.display = 'none';
    }

    getCurrentVehicleProfile() {
        const manufacturer = document.getElementById('manufacturerSelector').value;
        const model = document.getElementById('modelSelector').value;
        const generation = document.getElementById('generationSelector').value;
        const body = document.getElementById('bodySelector').value;
        const transmission = document.getElementById('transmissionSelector').value;

        return `${manufacturer} ${model} ${generation} ${body} ${transmission}`.replace(/\s+/g, ' ').trim();
    }

    showAuditLog() {
        // TODO: Implement audit log viewer modal
        this.showNotification('Audit log viewer coming soon', 'info');
    }
    const panel = document.getElementById('capabilitiesPanel');

    if(!capabilities || capabilities.status === 'UNKNOWN') {
    panel.style.display = 'none';
    return;
}

panel.style.display = 'block';

// Update interface information
document.getElementById('requiredInterface').textContent = capabilities.interface?.required || '-';
document.getElementById('vehicleProtocol').textContent = capabilities.interface?.protocol || '-';
document.getElementById('interfaceNotes').textContent = capabilities.interface?.notes || '-';

// Update modules
const moduleList = document.getElementById('moduleList');
moduleList.innerHTML = '';

if (capabilities.modules) {
    Object.entries(capabilities.modules).forEach(([module, info]) => {
        const item = document.createElement('div');
        item.className = 'module-item';

        const name = document.createElement('span');
        name.className = 'module-name';
        name.textContent = module;

        const status = document.createElement('span');
        status.className = `status-badge ${info.supported ? 'supported' : 'not-supported'}`;
        status.textContent = info.status;

        item.appendChild(name);
        item.appendChild(status);
        moduleList.appendChild(item);
    });
}

// Update services
const serviceList = document.getElementById('serviceList');
serviceList.innerHTML = '';

if (capabilities.services) {
    Object.entries(capabilities.services).forEach(([service, info]) => {
        const item = document.createElement('div');
        item.className = 'service-item';

        const name = document.createElement('span');
        name.className = 'service-name';
        name.textContent = service.replace('_', ' ');

        const status = document.createElement('span');
        status.className = `status-badge ${info.supported ? 'supported' : 'not-supported'}`;
        status.textContent = info.status;

        item.appendChild(name);
        item.appendChild(status);
        serviceList.appendChild(item);
    });
}

// Update special features
document.getElementById('virtualDynoSupport').className =
    `status-badge ${capabilities.features?.virtual_dyno ? 'supported' : 'not-supported'}`;
document.getElementById('virtualDynoSupport').textContent =
    capabilities.features?.virtual_dyno ? 'SUPPORTED' : 'NOT SUPPORTED';

document.getElementById('dsgShiftSupport').className =
    `status-badge ${capabilities.features?.dsg_shifts ? 'supported' : 'not-supported'}`;
document.getElementById('dsgShiftSupport').textContent =
    capabilities.features?.dsg_shifts ? 'SUPPORTED' : 'NOT SUPPORTED';

document.getElementById('awdModelingSupport').className =
    `status-badge ${capabilities.features?.awd_modeling ? 'supported' : 'not-supported'}`;
document.getElementById('awdModelingSupport').textContent =
    capabilities.features?.awd_modeling ? 'SUPPORTED' : 'NOT SUPPORTED';

// Update confidence indicator
const confidenceElement = document.getElementById('capabilityConfidence').querySelector('.confidence-indicator');
confidenceElement.textContent = `${capabilities.confidence}% CONFIDENCE`;

if (capabilities.confidence >= 80) {
    confidenceElement.className = 'confidence-indicator high';
} else if (capabilities.confidence >= 60) {
    confidenceElement.className = 'confidence-indicator medium';
} else {
    confidenceElement.className = 'confidence-indicator low';
}
    }

getAuthToken() {
    // Get JWT token from localStorage or wherever it's stored
    return localStorage.getItem('authToken') || '';
}

loadPresetConstants(preset) {
    // Load constants into form fields
    document.getElementById('vehicleMass').value = preset.vehicle_mass;
    document.getElementById('vehicleMassDefault').textContent = preset.vehicle_mass;

    document.getElementById('driverFuelMass').value = preset.driver_fuel_estimate || 95;
    document.getElementById('dragCoefficient').value = preset.drag_coefficient;
    document.getElementById('frontalArea').value = preset.frontal_area;
    document.getElementById('rollingResistance').value = preset.rolling_resistance;
    document.getElementById('wheelRadius').value = preset.wheel_radius;
    document.getElementById('drivetrainEfficiency').value = preset.drivetrain_efficiency * 100;
    document.getElementById('finalDriveRatio').value = preset.final_drive_ratio;

    // Update drivetrain model panel
    this.updateDrivetrainModel(preset);

    // Mark all as unmodified initially
    document.querySelectorAll('.modified-indicator').forEach(indicator => {
        indicator.style.display = 'none';
    });
}

updateDrivetrainModel(preset) {
    // Update drivetrain layout display
    document.getElementById('drivetrainLayout').textContent = preset.drivetrain_type || 'Unknown';
    document.getElementById('transmissionType').textContent = preset.transmission_type || 'Unknown';

    // Update efficiency values
    const baseEfficiency = preset.drivetrain_efficiency || 0.85;
    document.getElementById('baseEfficiency').value = baseEfficiency;

    // Show/hide AWD controls
    const isAWD = ['AWD_HALDEX', 'AWD_FULL', 'AWD_PART_TIME'].includes(preset.drivetrain_type);
    const torqueSplitSection = document.getElementById('torqueSplitSection');
    const couplingLossItem = document.getElementById('couplingLossItem');

    if (isAWD) {
        torqueSplitSection.style.display = 'block';
        couplingLossItem.style.display = 'block';

        // Set torque split
        const frontSplit = preset.awd_torque_split_front || 0.5;
        document.getElementById('torqueSplitSlider').value = frontSplit * 100;
        this.updateTorqueSplitDisplay(frontSplit * 100);

        // Set coupling loss
        document.getElementById('couplingLoss').value = preset.coupling_loss_factor || 0.03;
    } else {
        torqueSplitSection.style.display = 'none';
        couplingLossItem.style.display = 'none';
    }

    // Update actual efficiency display
    this.updateActualEfficiency();
}

updateTorqueSplitDisplay(frontPercent) {
    const rearPercent = 100 - frontPercent;

    // Update bars
    document.getElementById('frontTorqueBar').style.width = frontPercent + '%';
    document.getElementById('rearTorqueBar').style.width = rearPercent + '%';

    // Update percentages
    document.getElementById('frontTorquePercent').textContent = frontPercent + '%';
    document.getElementById('rearTorquePercent').textContent = rearPercent + '%';

    // Update values
    document.getElementById('frontTorqueValue').textContent = frontPercent;
    document.getElementById('rearTorqueValue').textContent = rearPercent;
}

updateActualEfficiency() {
    const baseEfficiency = parseFloat(document.getElementById('baseEfficiency').value);
    const isAWD = document.getElementById('torqueSplitSection').style.display !== 'none';

    let actualEfficiency = baseEfficiency;

    if (isAWD) {
        const couplingLoss = parseFloat(document.getElementById('couplingLoss').value) || 0;
        const frontSplit = parseFloat(document.getElementById('torqueSplitSlider').value) / 100;

        // η_eff = η_base - k_coupling * (1 - α_front)
        actualEfficiency = baseEfficiency - couplingLoss * (1 - frontSplit);
    }

    document.getElementById('actualEfficiency').textContent = (actualEfficiency * 100).toFixed(1) + '%';
}

saveDrivetrainSettings() {
    // Collect current drivetrain settings
    const settings = {
        base_efficiency: parseFloat(document.getElementById('baseEfficiency').value),
        coupling_loss: parseFloat(document.getElementById('couplingLoss').value) || null,
        torque_split_front: parseFloat(document.getElementById('torqueSplitSlider').value) / 100,
        torque_split_rear: 1 - (parseFloat(document.getElementById('torqueSplitSlider').value) / 100)
    };

    // Validate settings
    if (settings.base_efficiency < 0.5 || settings.base_efficiency > 1.0) {
        this.showNotification('Base efficiency must be between 0.5 and 1.0', 'error');
        return;
    }

    if (settings.coupling_loss && (settings.coupling_loss < 0 || settings.coupling_loss > 0.2)) {
        this.showNotification('Coupling loss must be between 0 and 0.2', 'error');
        return;
    }

    // Save to current constants
    if (this.currentPreset) {
        this.currentPreset.drivetrain_efficiency = settings.base_efficiency;
        this.currentPreset.coupling_loss_factor = settings.coupling_loss;
        this.currentPreset.awd_torque_split_front = settings.torque_split_front;
        this.currentPreset.awd_torque_split_rear = settings.torque_split_rear;

        this.showNotification('Drivetrain settings saved to current preset', 'success');
    } else {
        this.showNotification('No vehicle preset loaded', 'warning');
    }
}

showNotification(message, type = 'info') {
    // Simple notification implementation
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: ${type === 'error' ? '#ff4444' : type === 'warning' ? '#ffaa00' : '#00aa00'};
            color: white;
            border-radius: 5px;
            z-index: 10000;
            animation: fadeIn 0.3s ease-out;
        `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

bindEvents() {
    // Tab navigation
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', (e) => {
            this.switchTab(e.target.dataset.tab);
        });
    });

    // Hierarchical selectors
    document.getElementById('manufacturerSelector').addEventListener('change', (e) => {
        this.onManufacturerChange(e.target.value);
    });

    document.getElementById('platformSelector').addEventListener('change', (e) => {
        this.onPlatformChange(e.target.value);
    });

    document.getElementById('modelSelector').addEventListener('change', (e) => {
        this.onModelChange(e.target.value);
    });

    document.getElementById('bodySelector').addEventListener('change', (e) => {
        this.onBodyChange(e.target.value);
    });

    document.getElementById('generationSelector').addEventListener('change', (e) => {
        this.onGenerationChange(e.target.value);
    });

    document.getElementById('variantSelector').addEventListener('change', (e) => {
        this.onVariantChange(e.target.value);
    });

    document.getElementById('transmissionSelector').addEventListener('change', (e) => {
        this.onTransmissionChange(e.target.value);
    });

    // Drivetrain model controls
    document.getElementById('baseEfficiency').addEventListener('input', () => {
        this.updateActualEfficiency();
    });

    document.getElementById('couplingLoss').addEventListener('input', () => {
        this.updateActualEfficiency();
    });

    document.getElementById('torqueSplitSlider').addEventListener('input', (e) => {
        this.updateTorqueSplitDisplay(e.target.value);
        this.updateActualEfficiency();
    });

    document.getElementById('saveDrivetrainBtn').addEventListener('click', () => {
        this.saveDrivetrainSettings();
    });

    // Import tab events
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFileUpload(files[0]);
        }
    });

    // File picker
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            this.handleFileUpload(e.target.files[0]);
        }
    });
}

switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

updateConfidenceDisplay(preset) {
    const confidenceDiv = document.getElementById('presetConfidence');
    const badge = document.getElementById('confidenceBadge');
    const details = document.getElementById('confidenceDetails');

    confidenceDiv.style.display = 'block';

    // Set badge
    const score = preset.confidence_score || 100;
    let level = 'HIGH';
    if (score < 70) level = 'LOW';
    else if (score < 90) level = 'MEDIUM';

    badge.textContent = level;
    badge.className = `confidence-badge ${level}`;

    // Show details if available
    if (score < 100) {
        details.innerHTML = '<ul>' +
            '<li>Assumed values present</li>' +
            '<li>Engineering estimates used</li>' +
            '</ul>';
    } else {
        details.innerHTML = '';
    }
}

    async handleFileUpload(file) {
    const format = file.name.endsWith('.csv') ? 'csv' : 'json';

    try {
        // Validate file
        const formData = new FormData();
        formData.append('file', file);
        formData.append('format', format);

        const response = await fetch('/api/vehicles/constants/import/validate', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.valid) {
            this.showValidationResult(result, file);
        } else {
            this.showValidationErrors(result);
        }
    } catch (error) {
        console.error('Upload failed:', error);
        alert('Upload failed. Please try again.');
    }
}

showValidationResult(result, file) {
    const panel = document.getElementById('validationPanel');
    const status = document.getElementById('validationStatus');
    const errors = document.getElementById('validationErrors');
    const warnings = document.getElementById('validationWarnings');
    const preview = document.getElementById('validationPreview');
    const actions = document.getElementById('validationActions');

    panel.style.display = 'block';

    // Status
    status.className = 'validation-status valid';
    status.textContent = '✓ File validation successful';

    // Warnings
    if (result.warnings && result.warnings.length > 0) {
        warnings.style.display = 'block';
        document.getElementById('warningsList').innerHTML =
            result.warnings.map(w => `<li>${w}</li>`).join('');
    } else {
        warnings.style.display = 'none';
    }

    // Preview
    preview.style.display = 'block';
    const preset = result.preset;
    document.getElementById('previewGrid').innerHTML = `
            <div class="preview-item">
                <span class="preview-label">Name</span>
                <span class="preview-value">${preset.name}</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">Manufacturer</span>
                <span class="preview-value">${preset.manufacturer}</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">Model</span>
                <span class="preview-value">${preset.model}</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">Year</span>
                <span class="preview-value">${preset.year}</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">Mass</span>
                <span class="preview-value">${preset.vehicle_mass} kg</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">Drag Coefficient</span>
                <span class="preview-value">${preset.drag_coefficient}</span>
            </div>
        `;

    // Actions
    actions.style.display = 'block';
    this.pendingImport = { file, format: file.name.endsWith('.csv') ? 'csv' : 'json' };
}

showValidationErrors(result) {
    const panel = document.getElementById('validationPanel');
    const status = document.getElementById('validationStatus');
    const errors = document.getElementById('validationErrors');
    const warnings = document.getElementById('validationWarnings');
    const preview = document.getElementById('validationPreview');
    const actions = document.getElementById('validationActions');

    panel.style.display = 'block';

    // Status
    status.className = 'validation-status invalid';
    status.textContent = '✗ File validation failed';

    // Errors
    errors.style.display = 'block';
    document.getElementById('errorsList').innerHTML =
        result.errors.map(e => `<li>${e}</li>`).join('');

    // Hide other sections
    warnings.style.display = 'none';
    preview.style.display = 'none';
    actions.style.display = 'none';
}

    async confirmImport() {
    if (!this.pendingImport) return;

    try {
        const formData = new FormData();
        formData.append('file', this.pendingImport.file);
        formData.append('format', this.pendingImport.format);

        const response = await fetch('/api/vehicles/constants/import', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            alert('Profile imported successfully!');
            this.cancelImport();
            this.loadHierarchy(); // Refresh the hierarchy
        } else {
            alert('Import failed: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Import failed:', error);
        alert('Import failed. Please try again.');
    }
}

cancelImport() {
    document.getElementById('validationPanel').style.display = 'none';
    document.getElementById('fileInput').value = '';
    this.pendingImport = null;
}

    async loadVehicles() {
    try {
        const vehicles = await window.api.getVehicles();
        const selector = document.getElementById('vehicleSelector');

        selector.innerHTML = '<option value="">Select Vehicle...</option>';
        vehicles.forEach(vehicle => {
            const option = document.createElement('option');
            option.value = vehicle.id;
            option.textContent = `${vehicle.year} ${vehicle.make} ${vehicle.model}`;
            selector.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load vehicles:', error);
    }
}

    async onVehicleChange(vehicleId) {
    if (!vehicleId) {
        this.clearForm();
        return;
    }

    try {
        // Load active constants for vehicle
        this.currentConstants = await window.api.getActiveVehicleConstants(vehicleId);
        this.currentVehicle = { id: vehicleId };

        // Update UI
        this.updateForm(this.currentConstants);
        this.updateVersionInfo(this.currentConstants);

        // Load version history
        await this.loadVersionHistory(vehicleId);
    } catch (error) {
        console.error('Failed to load vehicle constants:', error);
        if (error.message.includes('No active constants found')) {
            // Show message to create constants
            this.showNoConstantsMessage();
        }
    }
}

onPresetChange(presetId) {
    if (!presetId || !this.currentVehicle) return;

    const preset = this.presets.find(p => p.id == presetId);
    if (!preset) return;

    // Update form with preset values
    this.updateFormWithPreset(preset);

    // Mark all fields as modified
    this.markAllFieldsModified();
}

updateForm(constants) {
    const c = constants.constants;

    // Update input values
    document.getElementById('vehicleMass').value = c.vehicle_mass || '';
    document.getElementById('driverFuelMass').value = c.driver_fuel_estimate || '';
    document.getElementById('totalMass').value = c.total_mass || '';
    document.getElementById('dragCoeff').value = c.drag_coefficient || '';
    document.getElementById('frontalArea').value = c.frontal_area || '';
    document.getElementById('airDensity').value = c.air_density || '';
    document.getElementById('rollingCoeff').value = c.rolling_resistance || '';
    document.getElementById('wheelRadius').value = c.wheel_radius || '';
    document.getElementById('drivetrainEff').value = c.drivetrain_efficiency || '';
    document.getElementById('finalDriveRatio').value = c.final_drive_ratio || '';
    document.getElementById('roadGrade').value = c.road_grade || '';
    document.getElementById('gravity').value = c.gravity || '';

    // Gear ratios
    if (c.gear_ratios && c.gear_ratios.length >= 6) {
        document.getElementById('gear1').value = c.gear_ratios[0] || '';
        document.getElementById('gear2').value = c.gear_ratios[1] || '';
        document.getElementById('gear3').value = c.gear_ratios[2] || '';
        document.getElementById('gear4').value = c.gear_ratios[3] || '';
        document.getElementById('gear5').value = c.gear_ratios[4] || '';
        document.getElementById('gear6').value = c.gear_ratios[5] || '';
    }

    // Update preset selector
    if (constants.preset_id) {
        document.getElementById('presetSelector').value = constants.preset_id;
    }

    // Clear modification indicators
    this.clearModificationIndicators();
    this.modifiedFields.clear();
}

updateFormWithPreset(preset) {
    // Update input values with preset
    document.getElementById('vehicleMass').value = preset.vehicle_mass || '';
    document.getElementById('driverFuelMass').value = preset.driver_fuel_estimate || '';
    document.getElementById('dragCoeff').value = preset.drag_coefficient || '';
    document.getElementById('frontalArea').value = preset.frontal_area || '';
    document.getElementById('airDensity').value = preset.air_density || '';
    document.getElementById('rollingCoeff').value = preset.rolling_resistance || '';
    document.getElementById('wheelRadius').value = preset.wheel_radius || '';
    document.getElementById('drivetrainEff').value = preset.drivetrain_efficiency || '';
    document.getElementById('finalDriveRatio').value = preset.final_drive_ratio || '';
    document.getElementById('roadGrade').value = preset.road_grade || '';
    document.getElementById('gravity').value = preset.gravity || '';

    // Gear ratios
    const gearRatios = preset.gear_ratios || [];
    document.getElementById('gear1').value = gearRatios[0] || '';
    document.getElementById('gear2').value = gearRatios[1] || '';
    document.getElementById('gear3').value = gearRatios[2] || '';
    document.getElementById('gear4').value = gearRatios[3] || '';
    document.getElementById('gear5').value = gearRatios[4] || '';
    document.getElementById('gear6').value = gearRatios[5] || '';

    // Update total mass
    this.updateTotalMass();
}

updateVersionInfo(constants) {
    document.getElementById('activeVersion').textContent = `Version ${constants.version}`;
}

onFieldChange(input) {
    const fieldName = input.id;
    this.modifiedFields.add(fieldName);

    // Show modified indicator
    const indicator = document.getElementById(`${fieldName}Modified`);
    if (indicator) {
        indicator.classList.add('visible');
    }

    // Add modified class to input
    input.classList.add('modified');

    // Update total mass if relevant
    if (fieldName === 'vehicleMass' || fieldName === 'driverFuelMass') {
        this.updateTotalMass();
    }
}

updateTotalMass() {
    const vehicleMass = parseFloat(document.getElementById('vehicleMass').value) || 0;
    const driverFuelMass = parseFloat(document.getElementById('driverFuelMass').value) || 0;
    document.getElementById('totalMass').value = vehicleMass + driverFuelMass;
}

markAllFieldsModified() {
    const inputs = document.querySelectorAll('.neon-input:not([readonly])');
    inputs.forEach(input => {
        this.modifiedFields.add(input.id);
        const indicator = document.getElementById(`${input.id}Modified`);
        if (indicator) {
            indicator.classList.add('visible');
        }
        input.classList.add('modified');
    });
}

clearModificationIndicators() {
    document.querySelectorAll('.modified-indicator').forEach(indicator => {
        indicator.classList.remove('visible');
    });
    document.querySelectorAll('.neon-input').forEach(input => {
        input.classList.remove('modified');
    });
}

    async restoreDefaults() {
    if (!this.currentVehicle) {
        alert('Please select a vehicle first');
        return;
    }

    try {
        const result = await window.api.restoreDefaultConstants(this.currentVehicle.id);
        this.currentConstants = result;
        this.updateForm(result);
        this.updateVersionInfo(result);

        // Show success message
        this.showMessage('Mazda defaults restored successfully');
    } catch (error) {
        console.error('Failed to restore defaults:', error);
        alert('Failed to restore defaults: ' + error.message);
    }
}

    async saveConstants() {
    if (!this.currentVehicle) {
        alert('Please select a vehicle first');
        return;
    }

    if (this.modifiedFields.size === 0) {
        alert('No changes to save');
        return;
    }

    try {
        // Collect overrides
        const overrides = {};

        if (this.modifiedFields.has('vehicleMass')) {
            overrides.vehicle_mass = parseFloat(document.getElementById('vehicleMass').value);
        }
        if (this.modifiedFields.has('driverFuelMass')) {
            overrides.driver_fuel_estimate = parseFloat(document.getElementById('driverFuelMass').value);
        }
        if (this.modifiedFields.has('dragCoeff')) {
            overrides.drag_coefficient = parseFloat(document.getElementById('dragCoeff').value);
        }
        if (this.modifiedFields.has('frontalArea')) {
            overrides.frontal_area = parseFloat(document.getElementById('frontalArea').value);
        }
        if (this.modifiedFields.has('airDensity')) {
            overrides.air_density = parseFloat(document.getElementById('airDensity').value);
        }
        if (this.modifiedFields.has('rollingCoeff')) {
            overrides.rolling_resistance = parseFloat(document.getElementById('rollingCoeff').value);
        }
        if (this.modifiedFields.has('wheelRadius')) {
            overrides.wheel_radius = parseFloat(document.getElementById('wheelRadius').value);
        }
        if (this.modifiedFields.has('drivetrainEff')) {
            overrides.drivetrain_efficiency = parseFloat(document.getElementById('drivetrainEff').value);
        }
        if (this.modifiedFields.has('finalDriveRatio')) {
            overrides.final_drive_ratio = parseFloat(document.getElementById('finalDriveRatio').value);
        }
        if (this.modifiedFields.has('roadGrade')) {
            overrides.road_grade = parseFloat(document.getElementById('roadGrade').value);
        }

        // Gear ratios
        const gearFields = ['gear1', 'gear2', 'gear3', 'gear4', 'gear5', 'gear6'];
        const gearRatios = [];
        let hasGearOverrides = false;

        gearFields.forEach((field, index) => {
            if (this.modifiedFields.has(field)) {
                gearRatios[index] = parseFloat(document.getElementById(field).value);
                hasGearOverrides = true;
            } else {
                gearRatios[index] = parseFloat(document.getElementById(field).value);
            }
        });

        if (hasGearOverrides) {
            overrides.gear_ratios = gearRatios;
        }

        // Get selected preset
        const presetId = parseInt(document.getElementById('presetSelector').value);
        if (!presetId) {
            alert('Please select a preset');
            return;
        }

        // Create new constants version
        const data = {
            preset_id: presetId,
            note: document.getElementById('modificationNote').value || 'User modification',
            overrides: overrides
        };

        const result = await window.api.createVehicleConstants(this.currentVehicle.id, data);
        this.currentConstants = result;
        this.updateForm(result);
        this.updateVersionInfo(result);

        // Clear modification indicators
        this.clearModificationIndicators();
        this.modifiedFields.clear();

        // Clear note
        document.getElementById('modificationNote').value = '';

        // Show success message
        this.showMessage('Constants saved successfully');
    } catch (error) {
        console.error('Failed to save constants:', error);
        alert('Failed to save constants: ' + error.message);
    }
}

recalculateDyno() {
    if (!this.currentConstants) {
        alert('No constants available for dyno recalculation');
        return;
    }

    // Show confirmation dialog
    if (confirm('Recalculate all dyno runs with these constants? This will update existing results.')) {
        // TODO: Implement dyno recalculation
        alert('Dyno recalculation not yet implemented');
    }
}

    async loadVersionHistory(vehicleId) {
    try {
        const versions = await window.api.getVehicleConstants(vehicleId);
        this.renderVersionHistory(versions);
    } catch (error) {
        console.error('Failed to load version history:', error);
    }
}

renderVersionHistory(versions) {
    const list = document.getElementById('versionList');
    list.innerHTML = '';

    versions.forEach(version => {
        const item = document.createElement('div');
        item.className = 'version-item';
        if (version.is_active) {
            item.classList.add('active');
        }

        item.innerHTML = `
                <div class="version-info-left">
                    <div class="version-number">Version ${version.version}</div>
                    <div class="version-date">${new Date(version.created_at).toLocaleString()}</div>
                    ${version.note ? `<div class="version-note">${version.note}</div>` : ''}
                </div>
                ${!version.is_active ? '<button class="btn-link" onclick="vehicleConstants.activateVersion(' + version.id + ')">Activate</button>' : '<span class="version-active">Active</span>'}
            `;

        list.appendChild(item);
    });
}

    async activateVersion(versionId) {
    if (!this.currentVehicle) return;

    try {
        const result = await window.api.activateVehicleConstants(this.currentVehicle.id, versionId);
        this.currentConstants = result;
        this.updateForm(result);
        this.updateVersionInfo(result);
        await this.loadVersionHistory(this.currentVehicle.id);

        this.showMessage('Version activated successfully');
    } catch (error) {
        console.error('Failed to activate version:', error);
        alert('Failed to activate version: ' + error.message);
    }
}

showVersionHistory() {
    document.getElementById('versionHistoryPanel').style.display = 'block';
}

hideVersionHistory() {
    document.getElementById('versionHistoryPanel').style.display = 'none';
}

clearForm() {
    const inputs = document.querySelectorAll('.neon-input');
    inputs.forEach(input => {
        input.value = '';
    });

    this.clearModificationIndicators();
    this.modifiedFields.clear();

    document.getElementById('activeVersion').textContent = 'None';
    document.getElementById('versionList').innerHTML = '';
}

showNoConstantsMessage() {
    const message = `
            <div class="empty-state">
                <div class="empty-icon">⚙️</div>
                <div class="empty-text">No constants configured</div>
                <div class="empty-subtext">Select a preset and click Save Constants to create initial configuration</div>
            </div>
        `;

    // Show in the constants editor panel
    const panel = document.querySelector('#vehicle-constants .holo-panel:nth-child(2) .panel-content');
    panel.innerHTML = message;
}

showMessage(text) {
    // Simple message display - could be enhanced with a toast notification
    const message = document.createElement('div');
    message.className = 'success-message';
    message.textContent = text;
    message.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 255, 0, 0.1);
            border: 1px solid rgba(0, 255, 0, 0.3);
            color: #0f0;
            padding: 12px 20px;
            border-radius: 4px;
            z-index: 1000;
        `;

    document.body.appendChild(message);

    setTimeout(() => {
        document.body.removeChild(message);
    }, 3000);
}
}

// Main VersaTuner App Class
class VersaTunerApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.isConnected = false;
        this.liveDataInterval = null;
        this.gauges = {};

        this.init();
    }

    init() {
        try {
            // Initialize window controls
            this.initWindowControls();

            // Initialize navigation
            this.initNavigation();

            // Initialize buttons
            this.initButtons();

            // Initialize tab navigation
            this.initTabNavigation();

            // Start simulated data
            this.startSimulatedData();
        } catch (error) {
            console.error('Error during initialization:', error);
        } finally {
            // Hide loading overlay after a short delay regardless of errors
            setTimeout(() => {
                const loadingOverlay = document.getElementById('loadingOverlay');
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'none';
                }
            }, 1000);
        }
    }

    initWindowControls() {
        // Window control buttons
        const minimizeBtn = document.getElementById('minimizeWindow');
        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', () => {
                window.electronAPI.minimizeWindow();
            });
        }

        const maximizeBtn = document.getElementById('maximizeWindow');
        if (maximizeBtn) {
            maximizeBtn.addEventListener('click', () => {
                window.electronAPI.maximizeWindow();
            });
        }

        const closeBtn = document.getElementById('closeWindow');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                window.electronAPI.closeWindow();
            });
        }
    }

    initNavigation() {
        const sidebarItems = document.querySelectorAll('.sidebar-item');

        sidebarItems.forEach(item => {
            item.addEventListener('click', () => {
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });
    }

    switchSection(sectionName) {
        // Update sidebar active state
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Update content sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        this.currentSection = sectionName;

        // Initialize section-specific content
        this.initSectionContent(sectionName);
    }

    initSectionContent(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                this.updateDashboard();
                break;
            case 'tuning':
                this.initTuningInterface();
                break;
            case 'maps':
                this.initMapEditor();
                break;
            case 'diagnostics':
                this.initDiagnostics();
                break;
            case 'logging':
                this.initDataLogging();
                break;
            case 'performance':
                this.initPerformance();
                break;
            case 'dyno':
                this.initVirtualDyno();
                break;
            case 'vehicle-constants':
                // Initialize vehicle constants manager
                if (!window.vehicleConstants) {
                    window.vehicleConstants = new VehicleConstantsManager();
                }
                break;
            case 'flash':
                this.initFlashInterface();
                break;
            case 'security':
                this.initSecurityTools();
                break;
            case 'ai-learning':
                this.initAI();
                break;
            case 'preferences':
                this.initPreferences();
                break;
        }
    }

    initThemeSelector() {
        const themeSelector = document.getElementById('themeSelector');

        // Set current theme
        themeSelector.value = window.themeAPI.getCurrentTheme();

        themeSelector.addEventListener('change', (e) => {
            window.themeAPI.applyTheme(e.target.value);
        });

        // Listen for theme changes from main process
        window.electronAPI.onThemeChange((event, themeName) => {
            window.themeAPI.applyTheme(themeName);
            themeSelector.value = themeName;
        });
    }

    initGauges() {
        // Initialize circular gauges
        this.gauges.rpm = new CircularGauge('rpmGauge', {
            min: 0,
            max: 8000,
            unit: 'RPM',
            color: 'var(--color-theme)',
            thresholds: [
                { value: 6000, color: '#ef4444' },
                { value: 7000, color: '#f59e0b' }
            ]
        });

        this.gauges.boost = new CircularGauge('boostGauge', {
            min: -20,
            max: 30,
            unit: 'PSI',
            color: 'var(--color-theme)',
            thresholds: [
                { value: 20, color: '#ef4444' },
                { value: 25, color: '#f59e0b' }
            ]
        });

        this.gauges.afr = new CircularGauge('afrGauge', {
            min: 10,
            max: 20,
            unit: 'AFR',
            color: 'var(--color-theme)',
            thresholds: [
                { value: 12, color: '#ef4444' },
                { value: 18, color: '#f59e0b' }
            ]
        });
    }

    initButtons() {
        // User session buttons
        document.getElementById('loginBtn')?.addEventListener('click', () => {
            this.showLoginDialog();
        });

        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            this.logout();
        });

        // Connect button
        document.getElementById('connectBtn')?.addEventListener('click', () => {
            this.toggleConnection();
        });

        // Refresh button
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.refreshData();
        });
    }

    initTabNavigation() {
        // Tab navigation for sections with tabs
        const tabButtons = document.querySelectorAll('.tab-button');

        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;

                // Remove active class from all buttons and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });

                // Add active class to clicked button and corresponding content
                e.target.classList.add('active');
                const tabContent = document.getElementById(`${tabName}-tab`);
                if (tabContent) {
                    tabContent.classList.add('active');
                }
            });
        });
    }

    toggleConnection() {
        const btn = document.getElementById('connectBtn');
        const status = document.getElementById('connectionStatus');

        if (this.isConnected) {
            // Disconnect
            this.isConnected = false;
            btn.textContent = 'Connect';
            btn.classList.remove('connected');
            status.innerHTML = '<span class="status-dot disconnected"></span> Disconnected';
            status.classList.remove('connected');

            // Stop live data
            if (this.liveDataInterval) {
                clearInterval(this.liveDataInterval);
                this.liveDataInterval = null;
            }
        } else {
            // Connect
            this.isConnected = true;
            btn.textContent = 'Disconnect';
            btn.classList.add('connected');
            status.innerHTML = '<span class="status-dot connected"></span> Connected';
            status.classList.add('connected');

            // Start live data
            this.startLiveData();
        }
    }

    startLiveData() {
        this.liveDataInterval = setInterval(() => {
            this.updateLiveData();
        }, 100);
    }

    startSimulatedData() {
        // Simulate some initial data
        this.updateVehicleInfo();
        this.updateLiveData();
    }

    updateVehicleInfo() {
        document.getElementById('vinValue').textContent = 'JM1BL1UF5A12345678';
        document.getElementById('ecuValue').textContent = 'Mazdaspeed3 2.3L DISI';
        document.getElementById('softwareValue').textContent = 'V1.2.3.456';
        document.getElementById('hardwareValue').textContent = 'A2-345';
    }

    updateLiveData() {
        if (!this.isConnected) return;

        // Simulate live data
        const rpm = Math.floor(Math.random() * 2000) + 1000;
        const speed = Math.floor(Math.random() * 60) + 40;
        const throttle = Math.floor(Math.random() * 50) + 20;
        const boost = (Math.random() * 15 - 5).toFixed(1);
        const afr = (Math.random() * 4 + 12).toFixed(1);
        const iat = Math.floor(Math.random() * 30) + 40;

        // Update text values
        document.getElementById('rpmValue').textContent = rpm;
        document.getElementById('speedValue').textContent = `${speed} km/h`;
        document.getElementById('throttleValue').textContent = `${throttle}%`;
        document.getElementById('boostValue').textContent = `${boost} psi`;
        document.getElementById('afrValue').textContent = afr;
        document.getElementById('iatValue').textContent = `${iat}°C`;

        // Update gauges
        this.gauges.rpm.setValue(rpm);
        this.gauges.boost.setValue(parseFloat(boost));
        this.gauges.afr.setValue(parseFloat(afr));
    }

    refreshData() {
        if (this.isConnected) {
            this.updateLiveData();
        }
    }

    updateDashboard() {
        // Dashboard-specific updates
        console.log('Dashboard updated');
    }

    initTuningInterface() {
        // Initialize tuning interface
        console.log('Tuning interface initialized');
    }

    async loadVehicles() {
        try {
            const vehicles = await window.electronAPI.getVehicles();
            this.updateVehicleList(vehicles);
        } catch (error) {
            console.error('Error loading vehicles:', error);
            this.updateVehicleList([]);
        }
    }

    updateVehicleList(vehicles) {
        const vehicleList = document.getElementById('vehicleList');
        if (!vehicleList) return;

        if (vehicles.length === 0) {
            vehicleList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🚗</div>
                    <div class="empty-text">No vehicles found</div>
                    <div class="empty-subtext">Add a vehicle to get started</div>
                </div>
            `;
            return;
        }

        vehicleList.innerHTML = vehicles.map(vehicle => `
            <div class="vehicle-item" data-id="${vehicle.id}">
                <div class="vehicle-item-vin">${vehicle.vin}</div>
                <div class="vehicle-item-model">${vehicle.year} ${vehicle.make} ${vehicle.model}</div>
                <div class="vehicle-item-ecu">${vehicle.ecu_type}</div>
            </div>
        `).join('');

        // Add click handlers
        vehicleList.querySelectorAll('.vehicle-item').forEach(item => {
            item.addEventListener('click', () => {
                const vehicleId = parseInt(item.dataset.id);
                this.showVehicleDetails(vehicles.find(v => v.id === vehicleId));
            });
        });
    }

    async showVehicleDetails(vehicle) {
        const detailsPanel = document.getElementById('vehicleDetails');
        if (!detailsPanel || !vehicle) return;

        detailsPanel.innerHTML = `
            <div class="vehicle-detail-row">
                <span class="vehicle-detail-label">VIN:</span>
                <span class="vehicle-detail-value">${vehicle.vin}</span>
            </div>
            <div class="vehicle-detail-row">
                <span class="vehicle-detail-label">Year:</span>
                <span class="vehicle-detail-value">${vehicle.year}</span>
            </div>
            <div class="vehicle-detail-row">
                <span class="vehicle-detail-label">Make:</span>
                <span class="vehicle-detail-value">${vehicle.make}</span>
            </div>
            <div class="vehicle-detail-row">
                <span class="vehicle-detail-label">Model:</span>
                <span class="vehicle-detail-value">${vehicle.model}</span>
            </div>
            <div class="vehicle-detail-row">
                <span class="vehicle-detail-label">ECU Type:</span>
                <span class="vehicle-detail-value">${vehicle.ecu_type}</span>
            </div>
            <div class="vehicle-detail-row">
                <span class="vehicle-detail-label">Engine:</span>
                <span class="vehicle-detail-value">${vehicle.engine_type || 'N/A'}</span>
            </div>
            <div class="vehicle-detail-row">
                <span class="vehicle-detail-label">Transmission:</span>
                <span class="vehicle-detail-value">${vehicle.transmission || 'N/A'}</span>
            </div>
        `;
    }

    async showAddVehicleDialog() {
        // TODO: Implement proper dialog
        const vin = prompt('Enter VIN:');
        if (!vin) return;

        const year = prompt('Enter year:');
        const make = prompt('Enter make:');
        const model = prompt('Enter model:');
        const ecuType = prompt('Enter ECU type:');

        if (vin && year && make && model && ecuType) {
            try {
                await window.electronAPI.addVehicle({
                    vin,
                    year: parseInt(year),
                    make,
                    model,
                    ecu_type: ecuType
                });
                this.loadVehicles();
            } catch (error) {
                alert('Error adding vehicle: ' + error);
            }
        }
    }

    async loadCurrentUser() {
        try {
            const user = await window.electronAPI.getCurrentUser();
            this.updateUserDisplay(user);
        } catch (error) {
            console.error('Error loading current user:', error);
            this.updateUserDisplay({ username: 'Guest', role: 'Viewer' });
        }
    }

    updateUserDisplay(user) {
        const username = document.getElementById('currentUsername');
        const userRole = document.getElementById('currentUserRole');
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');

        if (username) username.textContent = user.username || 'Guest';
        if (userRole) userRole.textContent = user.role || 'Viewer';

        if (loginBtn && logoutBtn) {
            if (user.username && user.username !== 'Guest') {
                loginBtn.style.display = 'none';
                logoutBtn.style.display = 'inline-block';
            } else {
                loginBtn.style.display = 'inline-block';
                logoutBtn.style.display = 'none';
            }
        }
    }

    initDashboard() {
        // Initialize dashboard
        console.log('Dashboard initialized');
        this.loadVehicles();
        this.loadCurrentUser();
    }

    initDiagnostics() {
        // Initialize diagnostics
        console.log('Diagnostics initialized');
        this.loadDiagnostics();
    }

    async loadDiagnostics() {
        if (!this.currentVehicle) {
            // Try to load first vehicle if none selected
            const vehicles = await window.electronAPI.getVehicles();
            if (vehicles.length > 0) {
                this.currentVehicle = vehicles[0];
            }
        }

        if (this.currentVehicle) {
            this.loadDTCs();
        }
    }

    async loadDTCs() {
        if (!this.currentVehicle) return;

        try {
            const dtcs = await window.electronAPI.getDTCs(this.currentVehicle.id);
            this.updateDTCList(dtcs);
        } catch (error) {
            console.error('Error loading DTCs:', error);
            this.updateDTCList([]);
        }
    }

    updateDTCList(dtcs) {
        const dtcList = document.getElementById('dtcList');
        if (!dtcList) return;

        if (dtcs.length === 0) {
            dtcList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">✓</div>
                    <div class="empty-text">No DTCs found</div>
                    <div class="empty-subtext">All systems operational</div>
                </div>
            `;
            return;
        }

        dtcList.innerHTML = dtcs.map(dtc => `
            <div class="dtc-item severity-${dtc.severity.toLowerCase()}" data-id="${dtc.id}">
                <div class="dtc-item-code">${dtc.code}</div>
                <div class="dtc-item-description">${dtc.description}</div>
                <div class="dtc-item-meta">
                    <span class="dtc-item-time">${new Date(dtc.timestamp).toLocaleString()}</span>
                    <span class="dtc-item-severity">${dtc.severity}</span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        dtcList.querySelectorAll('.dtc-item').forEach(item => {
            item.addEventListener('click', () => {
                const dtcId = parseInt(item.dataset.id);
                this.showDTCDetails(dtcs.find(d => d.id === dtcId));
            });
        });
    }

    async showDTCDetails(dtc) {
        const detailsPanel = document.getElementById('dtcDetails');
        if (!detailsPanel || !dtc) return;

        detailsPanel.innerHTML = `
            <div class="dtc-detail-row">
                <span class="dtc-detail-label">Code:</span>
                <span class="dtc-detail-value">${dtc.code}</span>
            </div>
            <div class="dtc-detail-row">
                <span class="dtc-detail-label">Description:</span>
                <span class="dtc-detail-value">${dtc.description}</span>
            </div>
            <div class="dtc-detail-row">
                <span class="dtc-detail-label">Severity:</span>
                <span class="dtc-detail-value severity-${dtc.severity.toLowerCase()}">${dtc.severity}</span>
            </div>
            <div class="dtc-detail-row">
                <span class="dtc-detail-label">Detected:</span>
                <span class="dtc-detail-value">${new Date(dtc.detection_time).toLocaleString()}</span>
            </div>
            <div class="dtc-detail-row">
                <span class="dtc-detail-label">Status:</span>
                <span class="dtc-detail-value">${dtc.status || 'Active'}</span>
            </div>
        `;
    }

    initDataLogging() {
        // Initialize data logging
        console.log('Data logging initialized');
        this.loadLogs();
        this.loadTelemetrySessions();

        // Add log level filter handler
        const logFilter = document.getElementById('logLevelFilter');
        if (logFilter) {
            logFilter.addEventListener('change', () => this.loadLogs());
        }
    }

    async loadLogs() {
        try {
            const level = document.getElementById('logLevelFilter')?.value || 'all';
            const logs = await window.electronAPI.getLogs(level);
            this.updateLogList(logs);
        } catch (error) {
            console.error('Error loading logs:', error);
            this.updateLogList([]);
        }
    }

    updateLogList(logs) {
        const logList = document.getElementById('logList');
        if (!logList) return;

        if (logs.length === 0) {
            logList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <div class="empty-text">No logs available</div>
                    <div class="empty-subtext">Start logging to see data</div>
                </div>
            `;
            return;
        }

        logList.innerHTML = logs.map(log => `
            <div class="log-item level-${log.level.toLowerCase()}" data-id="${log.id}">
                <div class="log-item-level">${log.level}</div>
                <div class="log-item-module">${log.module}</div>
                <div class="log-item-message">${log.message}</div>
                <div class="log-item-time">${new Date(log.timestamp).toLocaleString()}</div>
            </div>
        `).join('');

        // Add click handlers
        logList.querySelectorAll('.log-item').forEach(item => {
            item.addEventListener('click', () => {
                const logId = parseInt(item.dataset.id);
                this.showLogDetails(logs.find(l => l.id === logId));
            });
        });
    }

    async showLogDetails(log) {
        const detailsPanel = document.getElementById('logDetails');
        if (!detailsPanel || !log) return;

        detailsPanel.innerHTML = `
            <div class="log-detail-row">
                <span class="log-detail-label">Level:</span>
                <span class="log-detail-value level-${log.level.toLowerCase()}">${log.level}</span>
            </div>
            <div class="log-detail-row">
                <span class="log-detail-label">Module:</span>
                <span class="log-detail-value">${log.module}</span>
            </div>
            <div class="log-detail-row">
                <span class="log-detail-label">Message:</span>
                <span class="log-detail-value">${log.message}</span>
            </div>
            <div class="log-detail-row">
                <span class="log-detail-label">Timestamp:</span>
                <span class="log-detail-value">${new Date(log.timestamp).toLocaleString()}</span>
            </div>
            ${log.vehicle_id ? `
            <div class="log-detail-row">
                <span class="log-detail-label">Vehicle ID:</span>
                <span class="log-detail-value">${log.vehicle_id}</span>
            </div>
            ` : ''}
        `;
    }

    async loadTelemetrySessions() {
        if (!this.currentVehicle) {
            const vehicles = await window.electronAPI.getVehicles();
            if (vehicles.length > 0) {
                this.currentVehicle = vehicles[0];
            }
        }

        if (this.currentVehicle) {
            this.loadTelemetrySessionsForVehicle();
        }
    }

    async loadTelemetrySessionsForVehicle() {
        if (!this.currentVehicle) return;

        try {
            const sessions = await window.electronAPI.getTelemetrySessions(this.currentVehicle.id);
            this.updateTelemetrySessionList(sessions);
        } catch (error) {
            console.error('Error loading telemetry sessions:', error);
            this.updateTelemetrySessionList([]);
        }
    }

    updateTelemetrySessionList(sessions) {
        const sessionList = document.getElementById('telemetryList');
        const sessionCount = document.getElementById('sessionCount');

        if (!sessionList) return;

        if (sessionCount) {
            sessionCount.textContent = `${sessions.length} session${sessions.length !== 1 ? 's' : ''}`;
        }

        if (sessions.length === 0) {
            sessionList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📡</div>
                    <div class="empty-text">No telemetry sessions</div>
                    <div class="empty-subtext">Start a session to record data</div>
                </div>
            `;
            return;
        }

        sessionList.innerHTML = sessions.map(session => `
            <div class="telemetry-item" data-id="${session.id}">
                <div class="telemetry-item-name">${session.name || 'Telemetry Session'}</div>
                <div class="telemetry-item-date">${new Date(session.start_time).toLocaleString()}</div>
                <div class="telemetry-item-meta">
                    <span class="telemetry-item-duration">${session.duration || 'Active'}</span>
                    <span class="telemetry-item-count">${session.data_points || 0} points</span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        sessionList.querySelectorAll('.telemetry-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = parseInt(item.dataset.id);
                this.showTelemetrySessionDetails(sessions.find(s => s.id === sessionId));
            });
        });
    }

    async showTelemetrySessionDetails(session) {
        const detailsPanel = document.getElementById('telemetryDetails');
        if (!detailsPanel || !session) return;

        detailsPanel.innerHTML = `
            <div class="telemetry-detail-row">
                <span class="telemetry-detail-label">Name:</span>
                <span class="telemetry-detail-value">${session.name || 'Telemetry Session'}</span>
            </div>
            <div class="telemetry-detail-row">
                <span class="telemetry-detail-label">Start Time:</span>
                <span class="telemetry-detail-value">${new Date(session.start_time).toLocaleString()}</span>
            </div>
            <div class="telemetry-detail-row">
                <span class="telemetry-detail-label">Duration:</span>
                <span class="telemetry-detail-value">${session.duration || 'Active'}</span>
            </div>
            <div class="telemetry-detail-row">
                <span class="telemetry-detail-label">Data Points:</span>
                <span class="telemetry-detail-value">${session.data_points || 0}</span>
            </div>
            ${session.end_time ? `
            <div class="telemetry-detail-row">
                <span class="telemetry-detail-label">End Time:</span>
                <span class="telemetry-detail-value">${new Date(session.end_time).toLocaleString()}</span>
            </div>
            ` : ''}
        `;
    }

    initPerformance() {
        // Initialize performance tracking
        console.log('Performance initialized');
        this.loadPerformanceRuns();
    }

    async loadPerformanceRuns() {
        if (!this.currentVehicle) {
            const vehicles = await window.electronAPI.getVehicles();
            if (vehicles.length > 0) {
                this.currentVehicle = vehicles[0];
            }
        }

        if (this.currentVehicle) {
            this.loadPerformanceRunsForVehicle();
        }
    }

    async loadPerformanceRunsForVehicle() {
        if (!this.currentVehicle) return;

        try {
            const runs = await window.electronAPI.getPerformanceRuns(this.currentVehicle.id);
            this.updatePerformanceRunList(runs);
        } catch (error) {
            console.error('Error loading performance runs:', error);
            this.updatePerformanceRunList([]);
        }
    }

    updatePerformanceRunList(runs) {
        const runList = document.getElementById('performanceRunList');
        if (!runList) return;

        if (runs.length === 0) {
            runList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🏁</div>
                    <div class="empty-text">No performance runs</div>
                    <div class="empty-subtext">Start a performance run to track data</div>
                </div>
            `;
            return;
        }

        runList.innerHTML = runs.map(run => `
            <div class="run-item" data-id="${run.id}">
                <div class="run-item-name">${run.run_type || 'Performance Run'}</div>
                <div class="run-item-date">${new Date(run.start_time).toLocaleString()}</div>
                <div class="run-item-meta">
                    <span class="run-item-duration">${run.duration || 'N/A'}s</span>
                    <span class="run-item-result">${run.result || 'Completed'}</span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        runList.querySelectorAll('.run-item').forEach(item => {
            item.addEventListener('click', () => {
                const runId = parseInt(item.dataset.id);
                this.showPerformanceRunDetails(runs.find(r => r.id === runId));
            });
        });
    }

    async showPerformanceRunDetails(run) {
        const detailsPanel = document.getElementById('performanceRunDetails');
        if (!detailsPanel || !run) return;

        detailsPanel.innerHTML = `
            <div class="run-detail-row">
                <span class="run-detail-label">Run Type:</span>
                <span class="run-detail-value">${run.run_type || 'Performance Run'}</span>
            </div>
            <div class="run-detail-row">
                <span class="run-detail-label">Start Time:</span>
                <span class="run-detail-value">${new Date(run.start_time).toLocaleString()}</span>
            </div>
            <div class="run-detail-row">
                <span class="run-detail-label">Duration:</span>
                <span class="run-detail-value">${run.duration || 'N/A'} seconds</span>
            </div>
            <div class="run-detail-row">
                <span class="run-detail-label">Result:</span>
                <span class="run-detail-value">${run.result || 'Completed'}</span>
            </div>
            ${run.notes ? `
            <div class="run-detail-row">
                <span class="run-detail-label">Notes:</span>
                <span class="run-detail-value">${run.notes}</span>
            </div>
            ` : ''}
        `;
    }

    initSecurityTools() {
        // Initialize security tools
        console.log('Security tools initialized');
        this.loadSecurityEvents();

        // Add security filter handler
        const securityFilter = document.getElementById('securityFilter');
        if (securityFilter) {
            securityFilter.addEventListener('change', () => this.loadSecurityEvents());
        }
    }

    async loadSecurityEvents() {
        try {
            const eventType = document.getElementById('securityFilter')?.value || 'all';
            const events = await window.electronAPI.getSecurityEvents(eventType);
            this.updateSecurityEventList(events);
        } catch (error) {
            console.error('Error loading security events:', error);
            this.updateSecurityEventList([]);
        }
    }

    updateSecurityEventList(events) {
        const eventList = document.getElementById('securityList');
        if (!eventList) return;

        if (events.length === 0) {
            eventList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔒</div>
                    <div class="empty-text">No security events</div>
                    <div class="empty-subtext">Security events will appear here</div>
                </div>
            `;
            return;
        }

        eventList.innerHTML = events.map(event => `
            <div class="security-item ${event.success ? 'success' : 'failure'}" data-id="${event.id}">
                <div class="security-item-type">${event.event_type}</div>
                <div class="security-item-description">${event.description}</div>
                <div class="security-item-meta">
                    <span class="security-item-time">${new Date(event.timestamp).toLocaleString()}</span>
                    <span class="security-item-success ${event.success ? 'success' : 'failure'}">
                        ${event.success ? 'Success' : 'Failed'}
                    </span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        eventList.querySelectorAll('.security-item').forEach(item => {
            item.addEventListener('click', () => {
                const eventId = parseInt(item.dataset.id);
                this.showSecurityEventDetails(events.find(e => e.id === eventId));
            });
        });
    }

    async showSecurityEventDetails(event) {
        const detailsPanel = document.getElementById('securityDetails');
        if (!detailsPanel || !event) return;

        detailsPanel.innerHTML = `
            <div class="security-detail-row">
                <span class="security-detail-label">Event Type:</span>
                <span class="security-detail-value">${event.event_type}</span>
            </div>
            <div class="security-detail-row">
                <span class="security-detail-label">Description:</span>
                <span class="security-detail-value">${event.description}</span>
            </div>
            <div class="security-detail-row">
                <span class="security-detail-label">Timestamp:</span>
                <span class="security-detail-value">${new Date(event.timestamp).toLocaleString()}</span>
            </div>
            <div class="security-detail-row">
                <span class="security-detail-label">Status:</span>
                <span class="security-detail-value ${event.success ? 'success' : 'failure'}">
                    ${event.success ? 'Success' : 'Failed'}
                </span>
            </div>
            ${event.user_id ? `
            <div class="security-detail-row">
                <span class="security-detail-label">User ID:</span>
                <span class="security-detail-value">${event.user_id}</span>
            </div>
            ` : ''}
        `;
    }

    initAI() {
        // Initialize AI & Learning
        console.log('AI & Learning initialized');
        this.loadAIModels();
        this.loadTrainingData();
    }

    initDyno() {
        // Initialize Virtual Dyno
        console.log('Virtual Dyno initialized');
        this.loadDynoRuns();
        this.initDynoCharts();
        this.initDynoEventHandlers();
    }

    initDynoCharts() {
        // Initialize chart placeholders
        this.torqueChart = null;
        this.powerChart = null;
        this.torqueComparisonChart = null;
        this.powerComparisonChart = null;
    }

    initDynoEventHandlers() {
        // Start dyno run button
        const startBtn = document.getElementById('startDynoBtn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startDynoRun());
        }

        // Compare runs button
        const compareBtn = document.getElementById('compareDynoBtn');
        if (compareBtn) {
            compareBtn.addEventListener('click', () => this.selectRunsForComparison());
        }

        // Close comparison button
        const closeComparisonBtn = document.getElementById('closeComparisonBtn');
        if (closeComparisonBtn) {
            closeComparisonBtn.addEventListener('click', () => {
                document.getElementById('comparisonPanel').style.display = 'none';
            });
        }

        // Smoothed curve checkboxes
        const showSmoothedTorque = document.getElementById('showSmoothedTorque');
        if (showSmoothedTorque) {
            showSmoothedTorque.addEventListener('change', () => this.updateTorqueChart());
        }

        const showSmoothedPower = document.getElementById('showSmoothedPower');
        if (showSmoothedPower) {
            showSmoothedPower.addEventListener('change', () => this.updatePowerChart());
        }

        // Physics details toggle
        const togglePhysicsBtn = document.getElementById('togglePhysicsDetails');
        if (togglePhysicsBtn) {
            togglePhysicsBtn.addEventListener('click', () => {
                const details = document.getElementById('physicsDetails');
                const isVisible = details.style.display !== 'none';
                details.style.display = isVisible ? 'none' : 'block';
                togglePhysicsBtn.textContent = isVisible ? 'Show Details' : 'Hide Details';

                if (!isVisible) {
                    this.updateForceChart();
                }
            });
        }

        // Vehicle config inputs
        const configInputs = ['vehicleMass', 'drivetrainLoss', 'tireRadius', 'finalDriveRatio'];
        configInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('change', () => this.updateDynoConfig());
            }
        });
    }

    async loadDynoRuns() {
        if (!this.currentVehicle) {
            const vehicles = await window.electronAPI.getVehicles();
            if (vehicles.length > 0) {
                this.currentVehicle = vehicles[0];
            }
        }

        if (this.currentVehicle) {
            try {
                const runs = await window.electronAPI.getDynoRuns(this.currentVehicle.id);
                this.updateDynoRunList(runs);
                this.updateDynoStatus(runs.length > 0 ? 'READY' : 'NO_DATA');
            } catch (error) {
                console.error('Error loading dyno runs:', error);
                this.updateDynoRunList([]);
            }
        }
    }

    updateDynoRunList(runs) {
        const runList = document.getElementById('dynoRunList');
        const runCount = document.getElementById('runCount');

        if (!runList) return;

        if (runCount) {
            runCount.textContent = `${runs.length} run${runs.length !== 1 ? 's' : ''}`;
        }

        if (runs.length === 0) {
            runList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📈</div>
                    <div class="empty-text">No dyno runs yet</div>
                    <div class="empty-subtext">Start a run to see results</div>
                </div>
            `;
            return;
        }

        runList.innerHTML = runs.map(run => `
            <div class="dyno-run-item" data-id="${run.id}">
                <div class="dyno-run-header">
                    <div class="dyno-run-name">Run ${run.id}</div>
                    <div class="dyno-run-status ${run.status.toLowerCase()}">${run.status}</div>
                </div>
                <div class="dyno-run-meta">
                    <span>${new Date(run.run_time).toLocaleString()}</span>
                    <span>Session ${run.telemetry_session_id}</span>
                </div>
                ${run.status === 'ACCEPTED' ? `
                <div class="dyno-run-stats">
                    <div class="dyno-run-stat">Peak: ${run.peak_torque?.toFixed(1) || '--'} Nm</div>
                    <div class="dyno-run-stat">Power: ${run.peak_power?.toFixed(1) || '--'} kW</div>
                    <div class="dyno-run-stat">Quality: ${run.data_quality_score?.toFixed(1) || '--'}%</div>
                </div>
                ` : ''}
                ${run.rejection_reason ? `
                <div class="dyno-run-rejection" style="color: #ff6666; font-size: 12px; margin-top: 8px;">
                    ${run.rejection_reason}
                </div>
                ` : ''}
            </div>
        `).join('');

        // Add click handlers
        runList.querySelectorAll('.dyno-run-item').forEach(item => {
            item.addEventListener('click', () => {
                const runId = parseInt(item.dataset.id);
                this.showDynoRunDetails(runs.find(r => r.id === runId));
            });
        });
    }

    async showDynoRunDetails(run) {
        if (!run) return;

        // Update status panel
        this.updateDynoStatus(run.status);

        if (run.status === 'REJECTED') {
            this.showSafetyViolations([run.rejection_reason]);
            return;
        }

        // Hide safety violations panel for accepted runs
        document.getElementById('safetyViolationsPanel').style.display = 'none';

        // Update input data status
        const inputStatus = run.sample_count > 0 ? 'COMPLETE' : 'INSUFFICIENT';
        document.getElementById('inputDataStatus').textContent = inputStatus;
        document.getElementById('inputDataStatus').className = `status-value ${inputStatus === 'COMPLETE' ? 'success' : 'error'}`;

        // Update pull detection
        const pullStatus = run.pull_start_time ? 'DETECTED' : 'NONE';
        document.getElementById('pullDetectionStatus').textContent = pullStatus;
        document.getElementById('pullDetectionStatus').className = `status-value ${pullStatus === 'DETECTED' ? 'success' : 'warning'}`;

        // Update safety check
        const safetyStatus = (run.knock_detected || run.over_temp_detected || run.unsafe_afr_detected) ? 'FAIL' : 'PASS';
        document.getElementById('safetyCheckStatus').textContent = safetyStatus;
        document.getElementById('safetyCheckStatus').className = `status-value ${safetyStatus === 'PASS' ? 'success' : 'error'}`;

        // Update data quality
        const qualityScore = run.data_quality_score || 0;
        document.getElementById('dataQualityStatus').textContent = `${qualityScore.toFixed(1)}%`;
        document.getElementById('dataQualityStatus').className = `status-value ${qualityScore >= 80 ? 'success' : qualityScore >= 60 ? 'warning' : 'error'}`;

        // Update peak values
        document.getElementById('peakTorque').textContent = `${run.peak_torque?.toFixed(1) || '--'} Nm`;
        document.getElementById('peakTorqueRPM').textContent = run.peak_torque_rpm?.toFixed(0) || '--';
        document.getElementById('peakPower').textContent = `${run.peak_power?.toFixed(1) || '--'} kW`;
        document.getElementById('peakPowerRPM').textContent = run.peak_power_rpm?.toFixed(0) || '--';

        // Update charts
        this.updateTorqueChart(run);
        this.updatePowerChart(run);
    }

    updateTorqueChart(run) {
        const canvas = document.getElementById('torqueChart');
        if (!canvas || !run) return;

        const ctx = canvas.getContext('2d');
        const showSmoothed = document.getElementById('showSmoothedTorque').checked;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw simple line chart
        const data = showSmoothed && run.smoothed_torque_curve ?
            run.smoothed_torque_curve : run.torque_curve;

        if (!data || data.length === 0) {
            // Draw no data message
            ctx.fillStyle = '#666';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', canvas.width / 2, canvas.height / 2);
            return;
        }

        // Scale data to canvas
        const padding = 40;
        const width = canvas.width - 2 * padding;
        const height = canvas.height - 2 * padding;

        const maxTorque = Math.max(...data.map(d => d[1])) * 1.1;
        const minRpm = Math.min(...data.map(d => d[0]));
        const maxRpm = Math.max(...data.map(d => d[0]));

        // Draw axes
        ctx.strokeStyle = '#444';
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();

        // Draw data line
        ctx.strokeStyle = '#00ffff';
        ctx.lineWidth = 2;
        ctx.beginPath();

        data.forEach((point, i) => {
            const x = padding + ((point[0] - minRpm) / (maxRpm - minRpm)) * width;
            const y = canvas.height - padding - (point[1] / maxTorque) * height;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // Draw labels
        ctx.fillStyle = '#ccc';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';

        // X-axis labels (RPM)
        for (let i = 0; i <= 5; i++) {
            const rpm = minRpm + (maxRpm - minRpm) * i / 5;
            const x = padding + (width * i / 5);
            ctx.fillText(rpm.toFixed(0), x, canvas.height - padding + 20);
        }

        // Y-axis labels (Torque)
        ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const torque = maxTorque * (1 - i / 5);
            const y = padding + (height * i / 5);
            ctx.fillText(torque.toFixed(0), padding - 10, y + 5);
        }
    }

    updatePowerChart(run) {
        const canvas = document.getElementById('powerChart');
        if (!canvas || !run) return;

        const ctx = canvas.getContext('2d');
        const showSmoothed = document.getElementById('showSmoothedPower').checked;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw simple line chart
        const data = showSmoothed && run.smoothed_power_curve ?
            run.smoothed_power_curve : run.power_curve;

        if (!data || data.length === 0) {
            // Draw no data message
            ctx.fillStyle = '#666';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', canvas.width / 2, canvas.height / 2);
            return;
        }

        // Scale data to canvas
        const padding = 40;
        const width = canvas.width - 2 * padding;
        const height = canvas.height - 2 * padding;

        const maxPower = Math.max(...data.map(d => d[1])) * 1.1;
        const minRpm = Math.min(...data.map(d => d[0]));
        const maxRpm = Math.max(...data.map(d => d[0]));

        // Draw axes
        ctx.strokeStyle = '#444';
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();

        // Draw data line
        ctx.strokeStyle = '#ff00ff';
        ctx.lineWidth = 2;
        ctx.beginPath();

        data.forEach((point, i) => {
            const x = padding + ((point[0] - minRpm) / (maxRpm - minRpm)) * width;
            const y = canvas.height - padding - (point[1] / maxPower) * height;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // Draw labels
        ctx.fillStyle = '#ccc';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';

        // X-axis labels (RPM)
        for (let i = 0; i <= 5; i++) {
            const rpm = minRpm + (maxRpm - minRpm) * i / 5;
            const x = padding + (width * i / 5);
            ctx.fillText(rpm.toFixed(0), x, canvas.height - padding + 20);
        }

        // Y-axis labels (Power)
        ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const power = maxPower * (1 - i / 5);
            const y = padding + (height * i / 5);
            ctx.fillText(power.toFixed(0), padding - 10, y + 5);
        }
    }

    updateDynoStatus(status) {
        const statusElement = document.getElementById('dynoStatus');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `panel-status ${status.toLowerCase()}`;
        }
    }

    showSafetyViolations(violations) {
        const panel = document.getElementById('safetyViolationsPanel');
        const list = document.getElementById('violationList');

        if (!panel || !list) return;

        panel.style.display = 'block';
        list.innerHTML = violations.map(v => `
            <div class="violation-item">${v}</div>
        `).join('');
    }

    async startDynoRun() {
        if (!this.currentVehicle) {
            alert('Please select a vehicle first');
            return;
        }

        // Get latest telemetry session
        const sessions = await window.electronAPI.getTelemetrySessions(this.currentVehicle.id);
        if (sessions.length === 0) {
            alert('No telemetry sessions available. Please log data first.');
            return;
        }

        const latestSession = sessions[0];

        // Create dyno run
        const result = await window.electronAPI.createDynoRun(
            this.currentVehicle.id,
            latestSession.id
        );

        if (!result.success) {
            alert(`Failed to create dyno run: ${result.error}`);
            return;
        }

        // Process the run
        this.updateDynoStatus('PROCESSING');
        const processResult = await window.electronAPI.processDynoRun(result.data.id);

        if (processResult.success) {
            // Reload runs
            this.loadDynoRuns();

            // Show the new run
            const runs = await window.electronAPI.getDynoRuns(this.currentVehicle.id);
            const newRun = runs.find(r => r.id === result.data.id);
            if (newRun) {
                this.showDynoRunDetails(newRun);
            }
        } else {
            this.updateDynoStatus('FAILED');
            alert(`Dyno processing failed: ${processResult.error}`);
        }
    }

    async selectRunsForComparison() {
        const runs = await window.electronAPI.getDynoRuns(this.currentVehicle?.id);
        const acceptedRuns = runs.filter(r => r.status === 'ACCEPTED');

        if (acceptedRuns.length < 2) {
            alert('Need at least 2 successful runs to compare');
            return;
        }

        // Simple selection - use the two most recent runs
        const run1 = acceptedRuns[0];
        const run2 = acceptedRuns[1];

        const comparison = await window.electronAPI.compareDynoRuns(run1.id, run2.id);

        if (comparison.success) {
            this.showComparison(comparison.data);
        } else {
            alert(`Comparison failed: ${comparison.error}`);
        }
    }

    showComparison(comparison) {
        const panel = document.getElementById('comparisonPanel');
        panel.style.display = 'block';

        // Update comparison summary
        const summary = document.getElementById('comparisonSummary');
        const diff = comparison.differences;

        summary.innerHTML = `
            <h3>Comparison Summary</h3>
            <div class="comparison-stats">
                <div class="comparison-stat">
                    <div class="comparison-stat-label">Torque Change</div>
                    <div class="comparison-stat-value ${diff.peak_torque_change >= 0 ? 'positive' : 'negative'}">
                        ${diff.peak_torque_change >= 0 ? '+' : ''}${diff.peak_torque_change.toFixed(1)} Nm
                    </div>
                </div>
                <div class="comparison-stat">
                    <div class="comparison-stat-label">Power Change</div>
                    <div class="comparison-stat-value ${diff.peak_power_change >= 0 ? 'positive' : 'negative'}">
                        ${diff.peak_power_change >= 0 ? '+' : ''}${diff.peak_power_change.toFixed(1)} kW
                    </div>
                </div>
                <div class="comparison-stat">
                    <div class="comparison-stat-label">Torque RPM Shift</div>
                    <div class="comparison-stat-value">
                        ${diff.peak_torque_rpm_change >= 0 ? '+' : ''}${diff.peak_torque_rpm_change.toFixed(0)} RPM
                    </div>
                </div>
                <div class="comparison-stat">
                    <div class="comparison-stat-label">Power RPM Shift</div>
                    <div class="comparison-stat-value">
                        ${diff.peak_power_rpm_change >= 0 ? '+' : ''}${diff.peak_power_rpm_change.toFixed(0)} RPM
                    </div>
                </div>
            </div>
        `;

        // Draw comparison charts (simplified)
        this.drawComparisonChart('torqueComparisonChart', comparison.run1.torque_curve, comparison.run2.torque_curve);
        this.drawComparisonChart('powerComparisonChart', comparison.run1.power_curve, comparison.run2.power_curve);
    }

    drawComparisonChart(canvasId, curve1, curve2) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (!curve1 || !curve2 || curve1.length === 0 || curve2.length === 0) {
            return;
        }

        // Scale data to canvas
        const padding = 40;
        const width = canvas.width - 2 * padding;
        const height = canvas.height - 2 * padding;

        const allData = [...curve1, ...curve2];
        const maxValue = Math.max(...allData.map(d => d[1])) * 1.1;
        const minRpm = Math.min(...allData.map(d => d[0]));
        const maxRpm = Math.max(...allData.map(d => d[0]));

        // Draw axes
        ctx.strokeStyle = '#444';
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();

        // Draw curve 1
        ctx.strokeStyle = '#00ffff';
        ctx.lineWidth = 2;
        ctx.beginPath();

        curve1.forEach((point, i) => {
            const x = padding + ((point[0] - minRpm) / (maxRpm - minRpm)) * width;
            const y = canvas.height - padding - (point[1] / maxValue) * height;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // Draw curve 2
        ctx.strokeStyle = '#ff00ff';
        ctx.lineWidth = 2;
        ctx.beginPath();

        curve2.forEach((point, i) => {
            const x = padding + ((point[0] - minRpm) / (maxRpm - minRpm)) * width;
            const y = canvas.height - padding - (point[1] / maxValue) * height;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // Draw legend
        ctx.fillStyle = '#00ffff';
        ctx.fillRect(canvas.width - 100, 20, 10, 10);
        ctx.fillStyle = '#ccc';
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';
        ctx.fillText('Run 1', canvas.width - 85, 29);

        ctx.fillStyle = '#ff00ff';
        ctx.fillRect(canvas.width - 100, 35, 10, 10);
        ctx.fillStyle = '#ccc';
        ctx.fillText('Run 2', canvas.width - 85, 44);
    }

    updateDynoConfig() {
        // Save vehicle configuration to user preferences or database
        const config = {
            vehicle_mass: parseFloat(document.getElementById('vehicleMass').value),
            drivetrain_loss: parseFloat(document.getElementById('drivetrainLoss').value),
            tire_radius: parseFloat(document.getElementById('tireRadius').value),
            final_drive_ratio: parseFloat(document.getElementById('finalDriveRatio').value)
        };

        // Store for future use
        this.dynoConfig = config;

        // Update parameter display
        this.updateParameterDisplay(config);

        console.log('Updated dyno config:', config);
    }

    updateParameterDisplay(config = null) {
        // Use provided config or current config
        const cfg = config || this.dynoConfig || {
            vehicle_mass: 1450,
            drivetrain_loss: 15,
            tire_radius: 0.3175,
            final_drive_ratio: 4.105
        };

        // Update parameter values in UI
        document.getElementById('paramMass').textContent = `${cfg.vehicle_mass} kg`;
        document.getElementById('paramCd').textContent = '0.33';  // Fixed for Mazdaspeed3
        document.getElementById('paramArea').textContent = '2.2 m²';  // Fixed for Mazdaspeed3
        document.getElementById('paramCrr').textContent = '0.01';  // Fixed assumption
        document.getElementById('paramEff').textContent = `${(100 - cfg.drivetrain_loss)}%`;
        document.getElementById('paramAirDensity').textContent = '1.225 kg/m³';  // Sea level
        document.getElementById('paramGrade').textContent = '0°';  // Flat road assumption

        // Update smoothing status
        const showSmoothed = document.getElementById('showSmoothedTorque').checked ||
            document.getElementById('showSmoothedPower').checked;
        document.getElementById('paramSmoothing').textContent = showSmoothed ? 'ON' : 'OFF';
    }

    updateForceChart() {
        const canvas = document.getElementById('forceChart');
        if (!canvas || !this.currentDynoRun) return;

        const ctx = canvas.getContext('2d');

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Get force data from samples
        const samples = this.currentDynoRun.samples || [];
        if (samples.length === 0) return;

        // Prepare data for stacked area chart
        const maxForce = Math.max(...samples.map(s =>
            Math.max(s.force_tractive || 0, s.force_rolling_resistance || 0,
                s.force_aerodynamic || 0, s.force_grade || 0)
        )) * 1.1;

        // Scale data to canvas
        const padding = 40;
        const width = canvas.width - 2 * padding;
        const height = canvas.height - 2 * padding;

        // Draw axes
        ctx.strokeStyle = '#444';
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();

        // Draw stacked force areas
        const colors = {
            rolling: 'rgba(255, 100, 100, 0.6)',
            aero: 'rgba(100, 255, 100, 0.6)',
            grade: 'rgba(100, 100, 255, 0.6)',
            tractive: 'rgba(255, 255, 100, 0.6)'
        };

        // Sample every nth point for clarity
        const step = Math.max(1, Math.floor(samples.length / 100));
        const sampledData = samples.filter((_, i) => i % step === 0);

        // Draw force components as stacked areas
        for (let i = 0; i < sampledData.length - 1; i++) {
            const sample = sampledData[i];
            const nextSample = sampledData[i + 1];

            const x1 = padding + (i / (sampledData.length - 1)) * width;
            const x2 = padding + ((i + 1) / (sampledData.length - 1)) * width;

            // Rolling resistance (bottom)
            const y1_rolling = canvas.height - padding;
            const y2_rolling = canvas.height - padding -
                ((sample.force_rolling_resistance || 0) / maxForce) * height;

            ctx.fillStyle = colors.rolling;
            ctx.fillRect(x1, y2_rolling, x2 - x1, y1_rolling - y2_rolling);

            // Aerodynamic drag
            const y2_aero = y2_rolling - ((sample.force_aerodynamic || 0) / maxForce) * height;

            ctx.fillStyle = colors.aero;
            ctx.fillRect(x1, y2_aero, x2 - x1, y2_rolling - y2_aero);

            // Grade force
            const y2_grade = y2_aero - ((sample.force_grade || 0) / maxForce) * height;

            ctx.fillStyle = colors.grade;
            ctx.fillRect(x1, y2_grade, x2 - x1, y2_aero - y2_grade);

            // Tractive force (total)
            const y2_tractive = canvas.height - padding -
                ((sample.force_tractive || 0) / maxForce) * height;

            ctx.fillStyle = colors.tractive;
            ctx.fillRect(x1, y2_tractive, x2 - x1, y2_grade - y2_tractive);
        }

        // Draw legend
        const legendY = 20;
        const legendItems = [
            { color: colors.rolling, label: 'Rolling Resistance' },
            { color: colors.aero, label: 'Aerodynamic Drag' },
            { color: colors.grade, label: 'Grade Force' },
            { color: colors.tractive, label: 'Net Tractive' }
        ];

        legendItems.forEach((item, i) => {
            const x = canvas.width - 180;
            const y = legendY + i * 20;

            ctx.fillStyle = item.color;
            ctx.fillRect(x, y, 15, 15);

            ctx.fillStyle = '#ccc';
            ctx.font = '11px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(item.label, x + 20, y + 12);
        });

        // Draw labels
        ctx.fillStyle = '#ccc';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';

        // Y-axis labels (Force)
        ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const force = maxForce * (1 - i / 5);
            const y = padding + (height * i / 5);
            ctx.fillText(`${force.toFixed(0)} N`, padding - 10, y + 5);
        }
    }

    async loadAIModels() {
        try {
            const models = await window.electronAPI.getAIModels();
            this.updateAIModelList(models);
        } catch (error) {
            console.error('Error loading AI models:', error);
            this.updateAIModelList([]);
        }
    }

    updateAIModelList(models) {
        const modelList = document.getElementById('aiModelList');
        const modelCount = document.getElementById('modelCount');

        if (!modelList) return;

        if (modelCount) {
            modelCount.textContent = `${models.length} model${models.length !== 1 ? 's' : ''}`;
        }

        if (models.length === 0) {
            modelList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🤖</div>
                    <div class="empty-text">No AI models trained</div>
                    <div class="empty-subtext">Train a model to get started</div>
                </div>
            `;
            return;
        }

        modelList.innerHTML = models.map(model => `
            <div class="ai-model-item" data-id="${model.id}">
                <div class="ai-model-name">${model.name}</div>
                <div class="ai-model-type">${model.model_type}</div>
                <div class="ai-model-status">${model.status || 'Ready'}</div>
            </div>
        `).join('');

        // Add click handlers
        modelList.querySelectorAll('.ai-model-item').forEach(item => {
            item.addEventListener('click', () => {
                const modelId = parseInt(item.dataset.id);
                this.showAIModelDetails(models.find(m => m.id === modelId));
            });
        });
    }

    async showAIModelDetails(model) {
        const detailsPanel = document.getElementById('aiModelDetails');
        if (!detailsPanel || !model) return;

        detailsPanel.innerHTML = `
            <div class="ai-detail-row">
                <span class="ai-detail-label">Name:</span>
                <span class="ai-detail-value">${model.name}</span>
            </div>
            <div class="ai-detail-row">
                <span class="ai-detail-label">Type:</span>
                <span class="ai-detail-value">${model.model_type}</span>
            </div>
            <div class="ai-detail-row">
                <span class="ai-detail-label">Status:</span>
                <span class="ai-detail-value">${model.status || 'Ready'}</span>
            </div>
            <div class="ai-detail-row">
                <span class="ai-detail-label">Created:</span>
                <span class="ai-detail-value">${new Date(model.created_at).toLocaleString()}</span>
            </div>
            ${model.version ? `
            <div class="ai-detail-row">
                <span class="ai-detail-label">Version:</span>
                <span class="ai-detail-value">${model.version}</span>
            </div>
            ` : ''}
        `;
    }

    async loadTrainingData() {
        try {
            const data = await window.electronAPI.getTrainingData();
            this.updateTrainingDataList(data);
        } catch (error) {
            console.error('Error loading training data:', error);
            this.updateTrainingDataList([]);
        }
    }

    updateTrainingDataList(data) {
        const dataList = document.getElementById('trainingDataList');
        const dataCount = document.getElementById('dataCount');

        if (!dataList) return;

        if (dataCount) {
            dataCount.textContent = `${data.length} dataset${data.length !== 1 ? 's' : ''}`;
        }

        if (data.length === 0) {
            dataList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <div class="empty-text">No training data</div>
                    <div class="empty-subtext">Collect data to train models</div>
                </div>
            `;
            return;
        }

        dataList.innerHTML = data.map(item => `
            <div class="training-data-item" data-id="${item.id}">
                <div class="training-data-name">${item.name || 'Dataset'}</div>
                <div class="training-data-type">${item.data_type}</div>
                <div class="training-data-size">${item.size || 'Unknown'} records</div>
            </div>
        `).join('');
    }

    initPreferences() {
        // Preferences already initialized in initThemeSelector
        console.log('Preferences initialized');
    }
}

// Circular Gauge Class
class CircularGauge {
    constructor(canvasId, options) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.options = {
            min: options.min || 0,
            max: options.max || 100,
            unit: options.unit || '',
            color: options.color || '#06b6d4',
            thresholds: options.thresholds || []
        };

        this.value = this.options.min;
        this.animationFrame = null;

        this.init();
    }

    init() {
        this.draw();
    }

    setValue(value) {
        if (value < this.options.min) value = this.options.min;
        if (value > this.options.max) value = this.options.max;

        this.animateToValue(value);
    }

    animateToValue(targetValue) {
        const startValue = this.value;
        const diff = targetValue - startValue;
        const duration = 300;
        const startTime = Date.now();

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOutQuad = 1 - (1 - progress) * (1 - progress);
            this.value = startValue + diff * easeOutQuad;

            this.draw();

            if (progress < 1) {
                this.animationFrame = requestAnimationFrame(animate);
            }
        };

        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }

        animate();
    }

    draw() {
        const { width, height } = this.canvas;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 20;

        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);

        // Draw background circle
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.lineWidth = 15;
        this.ctx.stroke();

        // Draw colored arc based on value
        const startAngle = -Math.PI / 2;
        const endAngle = startAngle + (this.value - this.options.min) /
            (this.options.max - this.options.min) * 2 * Math.PI;

        // Determine color based on thresholds
        let color = this.options.color;
        for (const threshold of this.options.thresholds) {
            if (this.value >= threshold.value) {
                color = threshold.color;
            }
        }

        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 15;
        this.ctx.lineCap = 'round';
        this.ctx.stroke();

        // Draw tick marks
        for (let i = 0; i <= 10; i++) {
            const angle = startAngle + (i / 10) * 2 * Math.PI;
            const x1 = centerX + Math.cos(angle) * (radius - 20);
            const y1 = centerY + Math.sin(angle) * (radius - 20);
            const x2 = centerX + Math.cos(angle) * (radius - 25);
            const y2 = centerY + Math.sin(angle) * (radius - 25);

            this.ctx.beginPath();
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();
        }

        // Draw value text
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = 'bold 24px monospace';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(Math.round(this.value), centerX, centerY - 10);

        // Draw unit text
        this.ctx.font = '12px monospace';
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        this.ctx.fillText(this.options.unit, centerX, centerY + 15);
    }
}

// Global function for modal close
function closeOverrideModal() {
    document.getElementById('overrideActivationModal').style.display = 'none';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new VersaTunerApp();
    app.init();
    // Make app globally available
    window.versaTunerApp = app;

    // Initialize admin overrides if user is admin
    if (window.app) {
        window.app.initAdminOverrides();
    }
});

// Handle menu events from main process
window.electronAPI.onThemeChange((event, theme) => {
    console.log('Theme changed to:', theme);
});

// Export for potential use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VersaTunerApp, CircularGauge };
}
