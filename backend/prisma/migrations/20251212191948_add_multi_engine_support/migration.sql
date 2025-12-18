-- CreateTable
CREATE TABLE "tuning_engines" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "capabilities" TEXT NOT NULL,
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "tuning_flash_jobs" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL DEFAULT 'versa',
    "sessionId" TEXT NOT NULL,
    "state" TEXT NOT NULL DEFAULT 'PREPARED',
    "progress" INTEGER NOT NULL DEFAULT 0,
    "checksumOk" BOOLEAN NOT NULL DEFAULT false,
    "validationOk" BOOLEAN NOT NULL DEFAULT false,
    "errorMessage" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "tuning_flash_jobs_engineId_fkey" FOREIGN KEY ("engineId") REFERENCES "tuning_engines" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tuning_flash_jobs_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "tuning_apply_sessions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "tuning_engine_actions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL DEFAULT 'versa',
    "actionId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "parameters" TEXT NOT NULL DEFAULT '{}',
    "requiresSafetyLevel" TEXT NOT NULL DEFAULT 'SIMULATE',
    CONSTRAINT "tuning_engine_actions_engineId_fkey" FOREIGN KEY ("engineId") REFERENCES "tuning_engines" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_tuning_apply_events" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL DEFAULT 'versa',
    "sessionId" TEXT NOT NULL,
    "featureId" TEXT,
    "mapName" TEXT,
    "paramName" TEXT,
    "beforeValue" TEXT,
    "afterValue" TEXT,
    "result" TEXT NOT NULL,
    "message" TEXT,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "tuning_apply_events_engineId_fkey" FOREIGN KEY ("engineId") REFERENCES "tuning_engines" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tuning_apply_events_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "tuning_apply_sessions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_tuning_apply_events" ("afterValue", "beforeValue", "featureId", "id", "mapName", "message", "paramName", "result", "sessionId", "timestamp") SELECT "afterValue", "beforeValue", "featureId", "id", "mapName", "message", "paramName", "result", "sessionId", "timestamp" FROM "tuning_apply_events";
DROP TABLE "tuning_apply_events";
ALTER TABLE "new_tuning_apply_events" RENAME TO "tuning_apply_events";
CREATE TABLE "new_tuning_maps" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL DEFAULT 'versa',
    "profileId" TEXT NOT NULL,
    "mapName" TEXT NOT NULL,
    "mapType" TEXT NOT NULL,
    "address" TEXT NOT NULL,
    "size" INTEGER NOT NULL,
    "dataType" TEXT NOT NULL,
    "description" TEXT,
    "units" TEXT,
    "conversionFactor" REAL NOT NULL DEFAULT 1.0,
    "minValue" REAL,
    "maxValue" REAL,
    "xAxis" TEXT DEFAULT '[]',
    "yAxis" TEXT DEFAULT '[]',
    "values" TEXT NOT NULL DEFAULT '[]',
    "rawBytes" TEXT,
    "category" TEXT NOT NULL DEFAULT 'General',
    "isReadonly" BOOLEAN NOT NULL DEFAULT false,
    "isRuntimeAdjustable" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "tuning_maps_engineId_fkey" FOREIGN KEY ("engineId") REFERENCES "tuning_engines" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tuning_maps_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_tuning_maps" ("address", "category", "conversionFactor", "createdAt", "dataType", "description", "id", "isReadonly", "isRuntimeAdjustable", "mapName", "mapType", "maxValue", "minValue", "profileId", "rawBytes", "size", "units", "updatedAt", "values", "xAxis", "yAxis") SELECT "address", "category", "conversionFactor", "createdAt", "dataType", "description", "id", "isReadonly", "isRuntimeAdjustable", "mapName", "mapType", "maxValue", "minValue", "profileId", "rawBytes", "size", "units", "updatedAt", "values", "xAxis", "yAxis" FROM "tuning_maps";
DROP TABLE "tuning_maps";
ALTER TABLE "new_tuning_maps" RENAME TO "tuning_maps";
CREATE TABLE "new_tuning_apply_sessions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL DEFAULT 'versa',
    "vehicleSessionId" TEXT NOT NULL,
    "changesetId" TEXT,
    "mode" TEXT NOT NULL,
    "armed" BOOLEAN NOT NULL DEFAULT false,
    "expiresAt" DATETIME,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "applyToken" TEXT,
    "revertReason" TEXT,
    CONSTRAINT "tuning_apply_sessions_engineId_fkey" FOREIGN KEY ("engineId") REFERENCES "tuning_engines" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tuning_apply_sessions_changesetId_fkey" FOREIGN KEY ("changesetId") REFERENCES "tuning_changesets" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_tuning_apply_sessions" ("applyToken", "armed", "changesetId", "createdAt", "expiresAt", "id", "mode", "revertReason", "status", "updatedAt", "vehicleSessionId") SELECT "applyToken", "armed", "changesetId", "createdAt", "expiresAt", "id", "mode", "revertReason", "status", "updatedAt", "vehicleSessionId" FROM "tuning_apply_sessions";
DROP TABLE "tuning_apply_sessions";
ALTER TABLE "new_tuning_apply_sessions" RENAME TO "tuning_apply_sessions";
CREATE TABLE "new_tuning_changesets" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL DEFAULT 'versa',
    "profileId" TEXT NOT NULL,
    "author" TEXT NOT NULL,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "tuning_changesets_engineId_fkey" FOREIGN KEY ("engineId") REFERENCES "tuning_engines" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tuning_changesets_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_tuning_changesets" ("author", "createdAt", "id", "notes", "profileId") SELECT "author", "createdAt", "id", "notes", "profileId" FROM "tuning_changesets";
DROP TABLE "tuning_changesets";
ALTER TABLE "new_tuning_changesets" RENAME TO "tuning_changesets";
CREATE TABLE "new_tuning_profiles" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "engineId" TEXT NOT NULL DEFAULT 'versa',
    "ecuId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT false,
    "isBase" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "version" TEXT,
    "author" TEXT,
    "category" TEXT,
    "metadata" TEXT DEFAULT '{}',
    CONSTRAINT "tuning_profiles_engineId_fkey" FOREIGN KEY ("engineId") REFERENCES "tuning_engines" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tuning_profiles_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_tuning_profiles" ("author", "category", "createdAt", "description", "ecuId", "id", "isActive", "isBase", "metadata", "name", "updatedAt", "version") SELECT "author", "category", "createdAt", "description", "ecuId", "id", "isActive", "isBase", "metadata", "name", "updatedAt", "version" FROM "tuning_profiles";
DROP TABLE "tuning_profiles";
ALTER TABLE "new_tuning_profiles" RENAME TO "tuning_profiles";
CREATE UNIQUE INDEX "tuning_profiles_ecuId_name_key" ON "tuning_profiles"("ecuId", "name");
PRAGMA foreign_key_check;
PRAGMA foreign_keys=ON;

-- CreateIndex
CREATE UNIQUE INDEX "tuning_engine_actions_engineId_actionId_key" ON "tuning_engine_actions"("engineId", "actionId");
