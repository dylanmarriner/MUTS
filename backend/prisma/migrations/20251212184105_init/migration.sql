-- CreateTable
CREATE TABLE "ecus" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "vin" TEXT,
    "ecuType" TEXT NOT NULL,
    "protocol" TEXT NOT NULL,
    "firmwareVersion" TEXT,
    "hardwareVersion" TEXT,
    "serialNumber" TEXT,
    "securityAlgorithm" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "diagnostic_sessions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "startTime" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endTime" DATETIME,
    "status" TEXT NOT NULL,
    CONSTRAINT "diagnostic_sessions_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "dtcs" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "diagnosticSessionId" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "severity" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "occurrenceCount" INTEGER NOT NULL DEFAULT 1,
    "firstSeen" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastSeen" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "dtcs_diagnosticSessionId_fkey" FOREIGN KEY ("diagnosticSessionId") REFERENCES "diagnostic_sessions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "freeze_frames" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "diagnosticSessionId" TEXT NOT NULL,
    "dtcCode" TEXT NOT NULL,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "snapshot" TEXT NOT NULL DEFAULT '{}',
    CONSTRAINT "freeze_frames_diagnosticSessionId_fkey" FOREIGN KEY ("diagnosticSessionId") REFERENCES "diagnostic_sessions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "live_data" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "diagnosticSessionId" TEXT NOT NULL,
    "pid" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "value" REAL NOT NULL,
    "unit" TEXT,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "live_data_diagnosticSessionId_fkey" FOREIGN KEY ("diagnosticSessionId") REFERENCES "diagnostic_sessions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "tuning_profiles" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT false,
    "isBase" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "tuning_profiles_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "ignition_maps" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tuningProfileId" TEXT NOT NULL,
    "tableName" TEXT NOT NULL,
    "axisX" TEXT NOT NULL DEFAULT '[]',
    "axisY" TEXT NOT NULL DEFAULT '[]',
    "values" TEXT NOT NULL DEFAULT '[]',
    "description" TEXT,
    CONSTRAINT "ignition_maps_tuningProfileId_fkey" FOREIGN KEY ("tuningProfileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "fuel_maps" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tuningProfileId" TEXT NOT NULL,
    "tableName" TEXT NOT NULL,
    "axisX" TEXT NOT NULL DEFAULT '[]',
    "axisY" TEXT NOT NULL DEFAULT '[]',
    "values" TEXT NOT NULL DEFAULT '[]',
    "description" TEXT,
    CONSTRAINT "fuel_maps_tuningProfileId_fkey" FOREIGN KEY ("tuningProfileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "boost_maps" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tuningProfileId" TEXT NOT NULL,
    "tableName" TEXT NOT NULL,
    "axisX" TEXT NOT NULL DEFAULT '[]',
    "axisY" TEXT NOT NULL DEFAULT '[]',
    "values" TEXT NOT NULL DEFAULT '[]',
    "description" TEXT,
    CONSTRAINT "boost_maps_tuningProfileId_fkey" FOREIGN KEY ("tuningProfileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "limiter_maps" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tuningProfileId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "value" REAL NOT NULL,
    "unit" TEXT,
    "description" TEXT,
    CONSTRAINT "limiter_maps_tuningProfileId_fkey" FOREIGN KEY ("tuningProfileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "safety_checks" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tuningProfileId" TEXT NOT NULL,
    "parameter" TEXT NOT NULL,
    "minValue" REAL,
    "maxValue" REAL,
    "warningLevel" REAL,
    "criticalLevel" REAL,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT "safety_checks_tuningProfileId_fkey" FOREIGN KEY ("tuningProfileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "security_sessions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "level" TEXT NOT NULL,
    "seed" BLOB,
    "key" BLOB,
    "algorithm" TEXT,
    "success" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "security_sessions_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "flash_sessions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "fileName" TEXT NOT NULL,
    "fileHash" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "progress" REAL NOT NULL DEFAULT 0,
    "startTime" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endTime" DATETIME,
    "checksumValidated" BOOLEAN NOT NULL DEFAULT false,
    "rollbackAvailable" BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "flash_sessions_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "logs" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "fileName" TEXT NOT NULL,
    "format" TEXT NOT NULL,
    "startTime" DATETIME NOT NULL,
    "endTime" DATETIME,
    "size" INTEGER NOT NULL,
    "processed" BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "logs_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "dyno_results" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "logId" TEXT NOT NULL,
    "power" TEXT NOT NULL DEFAULT '{}',
    "torque" TEXT NOT NULL DEFAULT '{}',
    "peaks" TEXT NOT NULL DEFAULT '{}',
    CONSTRAINT "dyno_results_logId_fkey" FOREIGN KEY ("logId") REFERENCES "logs" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "torque_predictions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "logId" TEXT NOT NULL,
    "gear" INTEGER NOT NULL,
    "rpm" REAL NOT NULL,
    "torque" REAL NOT NULL,
    "confidence" REAL NOT NULL,
    CONSTRAINT "torque_predictions_logId_fkey" FOREIGN KEY ("logId") REFERENCES "logs" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "torque_advisories" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "gear" INTEGER NOT NULL,
    "maxTorque" REAL NOT NULL,
    "recommendedMax" REAL NOT NULL,
    "reason" TEXT,
    "basedOnLogId" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "torque_advisories_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "swas_configurations" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "reductionCurve" TEXT NOT NULL DEFAULT '{}',
    "activationAngle" REAL NOT NULL,
    "maxReduction" REAL NOT NULL,
    "responseTime" INTEGER NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "swas_configurations_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "agent_status" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "agentName" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "currentTask" TEXT,
    "lastUpdate" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "metadata" TEXT
);

-- CreateTable
CREATE TABLE "system_config" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "key" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "description" TEXT
);

-- CreateIndex
CREATE UNIQUE INDEX "ecus_vin_key" ON "ecus"("vin");

-- CreateIndex
CREATE UNIQUE INDEX "ecus_serialNumber_key" ON "ecus"("serialNumber");

-- CreateIndex
CREATE UNIQUE INDEX "dtcs_diagnosticSessionId_code_key" ON "dtcs"("diagnosticSessionId", "code");

-- CreateIndex
CREATE UNIQUE INDEX "tuning_profiles_ecuId_name_key" ON "tuning_profiles"("ecuId", "name");

-- CreateIndex
CREATE UNIQUE INDEX "dyno_results_logId_key" ON "dyno_results"("logId");

-- CreateIndex
CREATE UNIQUE INDEX "agent_status_agentName_key" ON "agent_status"("agentName");

-- CreateIndex
CREATE UNIQUE INDEX "system_config_key_key" ON "system_config"("key");
