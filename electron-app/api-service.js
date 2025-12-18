// API Service for communicating with FastAPI backend
const axios = require('axios');

class APIService {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8000';
        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: 5000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    // Health check
    async healthCheck() {
        try {
            const response = await this.client.get('/api/health');
            return response.data;
        } catch (error) {
            console.error('Health check failed:', error.message);
            return null;
        }
    }

    // Vehicle endpoints
    async getVehicles() {
        try {
            const response = await this.client.get('/api/vehicles');
            return response.data;
        } catch (error) {
            console.error('Error fetching vehicles:', error.message);
            return [];
        }
    }

    async createVehicle(vehicleData) {
        try {
            const response = await this.client.post('/api/vehicles', vehicleData);
            return response.data;
        } catch (error) {
            console.error('Error creating vehicle:', error.message);
            return { success: false, error: error.message };
        }
    }

    async deleteVehicle(vehicleId) {
        try {
            const response = await this.client.delete(`/api/vehicles/${vehicleId}`);
            return response.data;
        } catch (error) {
            console.error('Error deleting vehicle:', error.message);
            return { success: false, error: error.message };
        }
    }

    // DTC endpoints
    async getDTCs(vehicleId) {
        try {
            const response = await this.client.get(`/api/dtc/${vehicleId}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching DTCs:', error.message);
            return [];
        }
    }

    async createDTC(vehicleId, dtcData) {
        try {
            const response = await this.client.post(`/api/dtc/${vehicleId}`, dtcData);
            return response.data;
        } catch (error) {
            console.error('Error creating DTC:', error.message);
            return { success: false, error: error.message };
        }
    }

    async clearDTC(dtcId) {
        try {
            const response = await this.client.delete(`/api/dtc/${dtcId}`);
            return response.data;
        } catch (error) {
            console.error('Error clearing DTC:', error.message);
            return { success: false, error: error.message };
        }
    }

    // Log endpoints
    async getLogs(level = null, limit = 100) {
        try {
            const params = level && level !== 'all' ? { level, limit } : { limit };
            const response = await this.client.get('/api/logs', { params });
            return response.data;
        } catch (error) {
            console.error('Error fetching logs:', error.message);
            return [];
        }
    }

    async createLog(logData) {
        try {
            const response = await this.client.post('/api/logs', logData);
            return response.data;
        } catch (error) {
            console.error('Error creating log:', error.message);
            return { success: false, error: error.message };
        }
    }

    // Performance run endpoints
    async getPerformanceRuns(vehicleId) {
        try {
            const response = await this.client.get(`/api/performance-runs/${vehicleId}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching performance runs:', error.message);
            return [];
        }
    }

    async createPerformanceRun(vehicleId, runData) {
        try {
            const response = await this.client.post(`/api/performance-runs/${vehicleId}`, runData);
            return response.data;
        } catch (error) {
            console.error('Error creating performance run:', error.message);
            return { success: false, error: error.message };
        }
    }

    // Security event endpoints
    async getSecurityEvents(eventType = null, limit = 100) {
        try {
            const params = eventType && eventType !== 'all' ? { event_type: eventType, limit } : { limit };
            const response = await this.client.get('/api/security-events', { params });
            return response.data;
        } catch (error) {
            console.error('Error fetching security events:', error.message);
            return [];
        }
    }

    async createSecurityEvent(eventData) {
        try {
            const response = await this.client.post('/api/security-events', eventData);
            return response.data;
        } catch (error) {
            console.error('Error creating security event:', error.message);
            return { success: false, error: error.message };
        }
    }

    // AI model endpoints
    async getAIModels() {
        try {
            const response = await this.client.get('/api/ai-models');
            return response.data;
        } catch (error) {
            console.error('Error fetching AI models:', error.message);
            return [];
        }
    }

    async createAIModel(modelData) {
        try {
            const response = await this.client.post('/api/ai-models', modelData);
            return response.data;
        } catch (error) {
            console.error('Error creating AI model:', error.message);
            return { success: false, error: error.message };
        }
    }

    // Training data endpoints
    async getTrainingData(limit = 100) {
        try {
            const response = await this.client.get('/api/training-data', { params: { limit } });
            return response.data;
        } catch (error) {
            console.error('Error fetching training data:', error.message);
            return [];
        }
    }

    async createTrainingData(data) {
        try {
            const response = await this.client.post('/api/training-data', data);
            return response.data;
        } catch (error) {
            console.error('Error creating training data:', error.message);
            return { success: false, error: error.message };
        }
    }

    // Telemetry session endpoints
    async getTelemetrySessions(vehicleId) {
        try {
            const response = await this.client.get(`/api/telemetry-sessions/${vehicleId}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching telemetry sessions:', error.message);
            return [];
        }
    }

    async createTelemetrySession(vehicleId, sessionData) {
        try {
            const response = await this.client.post(`/api/telemetry-sessions/${vehicleId}`, sessionData);
            return response.data;
        } catch (error) {
            console.error('Error creating telemetry session:', error.message);
            return { success: false, error: error.message };
        }
    }

    // User session endpoints
    async getCurrentUser() {
        try {
            const response = await this.client.get('/api/current-user');
            return response.data;
        } catch (error) {
            console.error('Error fetching current user:', error.message);
            return { username: 'Guest', role: 'Viewer' };
        }
    }

    async login(credentials) {
        try {
            const response = await this.client.post('/api/login', credentials);
            return response.data;
        } catch (error) {
            console.error('Login failed:', error.message);
            return { success: false, error: 'Invalid credentials' };
        }
    }

    async logout() {
        try {
            const response = await this.client.post('/api/logout');
            return response.data;
        } catch (error) {
            console.error('Logout failed:', error.message);
            return { success: false, error: error.message };
        }
    }

    // Vehicle Constants
    async getConstantsPresets() {
        const response = await this.client.get('/api/vehicles/constants/presets');
        return response.data;
    }

    async getPresetHierarchy() {
        const response = await this.client.get('/api/vehicles/constants/hierarchy');
        return response.data;
    }

    async getVehicleConstants(vehicleId) {
        const response = await this.client.get(`/vehicles/${vehicleId}/constants`);
        return response.data;
    }

    async getActiveVehicleConstants(vehicleId) {
        const response = await this.client.get(`/vehicles/${vehicleId}/constants/active`);
        return response.data;
    }

    async createVehicleConstants(vehicleId, data) {
        const response = await this.client.post(`/vehicles/${vehicleId}/constants`, data);
        return response.data;
    }

    async activateVehicleConstants(vehicleId, constantsId) {
        const response = await this.client.put(`/vehicles/${vehicleId}/constants/${constantsId}/activate`);
        return response.data;
    }

    async restoreDefaultConstants(vehicleId) {
        const response = await this.client.post(`/vehicles/${vehicleId}/constants/restore-defaults`);
        return response.data;
    }

    // Dyno endpoints
    async createDynoRun(vehicleId, telemetrySessionId, tuningProfileId = null) {
        try {
            const params = new URLSearchParams({
                vehicle_id: vehicleId,
                telemetry_session_id: telemetrySessionId
            });
            if (tuningProfileId) {
                params.append('tuning_profile_id', tuningProfileId);
            }
            const response = await this.client.post(`/api/dyno/runs?${params}`);
            return response.data;
        } catch (error) {
            console.error('Error creating dyno run:', error.message);
            return { success: false, error: error.message };
        }
    }

    async processDynoRun(runId) {
        try {
            const response = await this.client.post(`/api/dyno/runs/${runId}/process`);
            return response.data;
        } catch (error) {
            console.error('Error processing dyno run:', error.message);
            return { success: false, error: error.message };
        }
    }

    async getDynoRuns(vehicleId = null) {
        try {
            const params = vehicleId ? { vehicle_id: vehicleId } : {};
            const response = await this.client.get('/api/dyno/runs', { params });
            return response.data;
        } catch (error) {
            console.error('Error fetching dyno runs:', error.message);
            return [];
        }
    }

    async getDynoRun(runId) {
        try {
            const response = await this.client.get(`/api/dyno/runs/${runId}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching dyno run:', error.message);
            return null;
        }
    }

    async compareDynoRuns(run1Id, run2Id) {
        try {
            const response = await this.client.get(`/api/dyno/runs/${run1Id}/compare/${run2Id}`);
            return response.data;
        } catch (error) {
            console.error('Error comparing dyno runs:', error.message);
            return { success: false, error: error.message };
        }
    }

    async getDynoSamples(runId) {
        try {
            const response = await this.client.get(`/api/dyno/runs/${runId}/samples`);
            return response.data;
        } catch (error) {
            console.error('Error fetching dyno samples:', error.message);
            return [];
        }
    }
}

module.exports = APIService;
