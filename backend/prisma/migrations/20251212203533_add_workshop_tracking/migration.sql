-- CreateTable
CREATE TABLE "technicians" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "certificationLevel" TEXT,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "jobs" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "vehicleId" TEXT NOT NULL,
    "ecuId" TEXT,
    "technicianId" TEXT NOT NULL,
    "operatorMode" TEXT NOT NULL,
    "startTime" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endTime" DATETIME,
    "status" TEXT NOT NULL DEFAULT 'open',
    "notes" TEXT,
    "vehicleInfo" TEXT DEFAULT '{}',
    "interfaceInfo" TEXT DEFAULT '{}',
    CONSTRAINT "jobs_technicianId_fkey" FOREIGN KEY ("technicianId") REFERENCES "technicians" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "jobs_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "job_events" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "jobId" TEXT NOT NULL,
    "technicianId" TEXT NOT NULL,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "category" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "payload" TEXT DEFAULT '{}',
    CONSTRAINT "job_events_jobId_fkey" FOREIGN KEY ("jobId") REFERENCES "jobs" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "job_events_technicianId_fkey" FOREIGN KEY ("technicianId") REFERENCES "technicians" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_flash_sessions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "ecuId" TEXT NOT NULL,
    "jobId" TEXT,
    "fileName" TEXT NOT NULL,
    "fileHash" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "progress" REAL NOT NULL DEFAULT 0,
    "startTime" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endTime" DATETIME,
    "checksumValidated" BOOLEAN NOT NULL DEFAULT false,
    "rollbackAvailable" BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "flash_sessions_ecuId_fkey" FOREIGN KEY ("ecuId") REFERENCES "ecus" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "flash_sessions_jobId_fkey" FOREIGN KEY ("jobId") REFERENCES "jobs" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_flash_sessions" ("checksumValidated", "ecuId", "endTime", "fileHash", "fileName", "id", "progress", "rollbackAvailable", "startTime", "status") SELECT "checksumValidated", "ecuId", "endTime", "fileHash", "fileName", "id", "progress", "rollbackAvailable", "startTime", "status" FROM "flash_sessions";
DROP TABLE "flash_sessions";
ALTER TABLE "new_flash_sessions" RENAME TO "flash_sessions";
PRAGMA foreign_key_check;
PRAGMA foreign_keys=ON;
