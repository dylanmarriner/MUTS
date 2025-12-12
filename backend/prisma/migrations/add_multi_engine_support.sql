-- Add multi-engine support to tuning platform
-- Migration: Add engine_id to existing tables and create new engine-specific tables

-- Create tuning_engines table first
CREATE TABLE "tuning_engines" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "capabilities" TEXT NOT NULL, -- JSON
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- Insert seed data for engines
INSERT INTO "tuning_engines" ("id", "name", "version", "capabilities") VALUES
('versa', 'VERSA Tuning Engine', '1.0.0', '{"supportedModes": ["SIMULATE", "LIVE_APPLY", "FLASH"], "supportsLiveApply": true, "supportsFlash": true, "supportsSimulation": true, "requiresArming": true, "maxMapSize": 65536, "supportedMapTypes": ["IGNITION", "FUEL", "BOOST", "VVT", "TORQUE", "LIMITER", "CORRECTION"]}'),
('cobb', 'COBB Tuning Engine', '1.0.0', '{"supportedModes": ["SIMULATE", "LIVE_APPLY", "FLASH"], "supportsLiveApply": true, "supportsFlash": true, "supportsSimulation": true, "requiresArming": true, "maxMapSize": 32768, "supportedMapTypes": ["IGNITION", "FUEL", "BOOST", "LIMITER"]}'),
('mds', 'MDS Diagnostic/Tuning Engine', '1.0.0', '{"supportedModes": ["SIMULATE", "LIVE_APPLY"], "supportsLiveApply": true, "supportsFlash": false, "supportsSimulation": true, "requiresArming": true, "maxMapSize": 16384, "supportedMapTypes": ["IGNITION", "FUEL", "DIAGNOSTIC"]}');

-- Add engine_id to existing tables with default 'versa'
ALTER TABLE "tuning_profiles" ADD COLUMN "engineId" TEXT NOT NULL DEFAULT 'versa';
ALTER TABLE "tuning_changesets" ADD COLUMN "engineId" TEXT NOT NULL DEFAULT 'versa';
ALTER TABLE "tuning_apply_sessions" ADD COLUMN "engineId" TEXT NOT NULL DEFAULT 'versa';
ALTER TABLE "tuning_maps" ADD COLUMN "engineId" TEXT NOT NULL DEFAULT 'versa';
ALTER TABLE "tuning_apply_events" ADD COLUMN "engineId" TEXT NOT NULL DEFAULT 'versa';

-- Create foreign key constraints
CREATE INDEX "tuning_profiles_engineId_idx" ON "tuning_profiles"("engineId");
CREATE INDEX "tuning_changesets_engineId_idx" ON "tuning_changesets"("engineId");
CREATE INDEX "tuning_apply_sessions_engineId_idx" ON "tuning_apply_sessions"("engineId");
CREATE INDEX "tuning_maps_engineId_idx" ON "tuning_maps"("engineId");
CREATE INDEX "tuning_apply_events_engineId_idx" ON "tuning_apply_events"("engineId");

-- Create tuning_flash_jobs table
CREATE TABLE "tuning_flash_jobs" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL,
    "sessionId" TEXT NOT NULL,
    "state" TEXT NOT NULL DEFAULT 'PREPARED',
    "progress" INTEGER NOT NULL DEFAULT 0,
    "checksumOk" BOOLEAN NOT NULL DEFAULT false,
    "validationOk" BOOLEAN NOT NULL DEFAULT false,
    "errorMessage" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    FOREIGN KEY ("engineId") REFERENCES "tuning_engines"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY ("sessionId") REFERENCES "tuning_apply_sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create indexes for flash_jobs
CREATE INDEX "tuning_flash_jobs_engineId_idx" ON "tuning_flash_jobs"("engineId");
CREATE INDEX "tuning_flash_jobs_sessionId_idx" ON "tuning_flash_jobs"("sessionId");
CREATE INDEX "tuning_flash_jobs_state_idx" ON "tuning_flash_jobs"("state");

-- Add engine-specific actions table for MDS requirements
CREATE TABLE "tuning_engine_actions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL,
    "actionId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "parameters" TEXT NOT NULL DEFAULT '{}', -- JSON
    "requiresSafetyLevel" TEXT NOT NULL DEFAULT 'SIMULATE',
    FOREIGN KEY ("engineId") REFERENCES "tuning_engines"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE("engineId", "actionId")
);

-- Insert MDS-specific actions
INSERT INTO "tuning_engine_actions" ("engineId", "actionId", "name", "description", "category", "requiresSafetyLevel") VALUES
('mds', 'adaptation_reset', 'Adaptation Reset', 'Reset fuel trims and learned adaptations', 'Diagnostics', 'LIVE_APPLY'),
('mds', 'injector_scaling', 'Injector Scaling', 'Scale injector values for new injectors', 'Calibration', 'LIVE_APPLY'),
('mds', 'maf_scaling', 'MAF Scaling', 'Scale MAF transfer function', 'Calibration', 'LIVE_APPLY'),
('mds', 'dtc_clear', 'Clear DTCs', 'Clear diagnostic trouble codes', 'Diagnostics', 'SIMULATE'),
('mds', 'force_regeneration', 'Force DPF Regeneration', 'Initiate DPF regeneration cycle', 'Procedures', 'LIVE_APPLY');

-- Update Prisma schema references in comments
-- Note: This SQL migration complements the Prisma schema update
