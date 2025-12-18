/*
  Warnings:

  - You are about to drop the column `updatedAt` on the `swas_configurations` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "tuning_profiles" ADD COLUMN "author" TEXT;
ALTER TABLE "tuning_profiles" ADD COLUMN "category" TEXT;
ALTER TABLE "tuning_profiles" ADD COLUMN "metadata" TEXT DEFAULT '{}';
ALTER TABLE "tuning_profiles" ADD COLUMN "version" TEXT;

-- CreateTable
CREATE TABLE "tuning_changesets" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "profileId" TEXT NOT NULL,
    "author" TEXT NOT NULL,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "tuning_changesets_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "tuning_apply_sessions" (
    "id" TEXT NOT NULL PRIMARY KEY,
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
    CONSTRAINT "tuning_apply_sessions_changesetId_fkey" FOREIGN KEY ("changesetId") REFERENCES "tuning_changesets" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "tuning_apply_events" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sessionId" TEXT NOT NULL,
    "featureId" TEXT,
    "mapName" TEXT,
    "paramName" TEXT,
    "beforeValue" TEXT,
    "afterValue" TEXT,
    "result" TEXT NOT NULL,
    "message" TEXT,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "tuning_apply_events_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "tuning_apply_sessions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "safety_snapshots" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sessionId" TEXT NOT NULL,
    "rpm" REAL NOT NULL,
    "boost" REAL NOT NULL,
    "afr" REAL NOT NULL,
    "knock" REAL NOT NULL,
    "coolant" REAL NOT NULL,
    "iat" REAL NOT NULL,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "throttle" REAL,
    "speed" REAL,
    "oilPressure" REAL,
    CONSTRAINT "safety_snapshots_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "tuning_apply_sessions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "tuning_maps" (
    "id" TEXT NOT NULL PRIMARY KEY,
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
    CONSTRAINT "tuning_maps_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "tuning_profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "tuning_map_changes" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "mapId" TEXT NOT NULL,
    "changesetId" TEXT NOT NULL,
    "xIndex" INTEGER,
    "yIndex" INTEGER,
    "oldValue" REAL,
    "newValue" REAL,
    "reason" TEXT,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "tuning_map_changes_mapId_fkey" FOREIGN KEY ("mapId") REFERENCES "tuning_maps" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tuning_map_changes_changesetId_fkey" FOREIGN KEY ("changesetId") REFERENCES "tuning_changesets" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_swas_configurations" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "reductionCurve" TEXT NOT NULL DEFAULT '{}',
    "activationAngle" REAL NOT NULL,
    "maxReduction" REAL NOT NULL,
    "responseTime" INTEGER NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "swas_configurations_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_swas_configurations" ("activationAngle", "createdAt", "ecuId", "enabled", "id", "maxReduction", "reductionCurve", "responseTime") SELECT "activationAngle", "createdAt", "ecuId", "enabled", "id", "maxReduction", "reductionCurve", "responseTime" FROM "swas_configurations";
DROP TABLE "swas_configurations";
ALTER TABLE "new_swas_configurations" RENAME TO "swas_configurations";
PRAGMA foreign_key_check;
PRAGMA foreign_keys=ON;
