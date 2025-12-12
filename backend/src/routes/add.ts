/**
 * ADD (Adaptive/AI/Decision) Routes
 * API endpoints for the ADD subsystem
 */

import { FastifyPluginAsync } from 'fastify';
import { Router } from 'express';
import { ADDManager } from '../modules/add';
import { LearningService } from '../modules/add/learning-service';
import { Prisma } from '@prisma/client';
import {
  TelemetryData,
  DiagnosticData,
  DecisionContext,
  SafetyLimits,
  Recommendation
} from '../modules/add/types';

const addRoutes: FastifyPluginAsync = async (fastify) => {
  let addManager: ADDManager;
  let learningService: LearningService;
  // const prisma = new PrismaClient(); // Commented out - not used in disabled routes

  // Initialize ADD manager
  fastify.post('/init', async (request, reply) => {
    try {
      if (!addManager) {
        addManager = new ADDManager(request.body as any || {});
        await addManager.initialize();
        }
      reply.send({ success: true, initialized: true });
    } catch (error) {
      reply.code(500).send({ error: error.message });
    }
  });

/*
// This file is disabled in index.ts - keeping original Express format
// The following code is commented out to avoid syntax errors
  const { technicianId, jobId, mode } = req.body;
    
    // Enforce LEARN_ONLY mode
    if (mode && mode !== 'LEARN_ONLY') {
      return res.status(403).json({ 
        error: 'Only LEARN_ONLY mode is supported for live learning',
        code: 'MODE_NOT_ALLOWED'
      });
    }

    const sessionId = await learningService.startSession(
      technicianId,
      jobId,
      'LEARN_ONLY'
    );

    res.json({ 
      success: true, 
      sessionId,
      mode: 'LEARN_ONLY',
      message: 'Learning session started in LEARN_ONLY mode - no ECU writes will be performed'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Stop current learning session
router.post('/learning/stop', async (req, res) => {
  try {
    if (!learningService) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    await learningService.stopSession();
    
    res.json({ 
      success: true, 
      message: 'Learning session stopped' 
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get current learning session
router.get('/learning/session', async (req, res) => {
  try {
    if (!learningService) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    const session = learningService.getCurrentSession();
    
    if (!session) {
      return res.json({ 
        active: false,
        message: 'No active learning session' 
      });
    }

    res.json({ 
      active: true,
      session: {
        sessionId: session.sessionId,
        technicianId: session.technicianId,
        jobId: session.jobId,
        mode: session.mode,
        startTime: session.startTime,
        sampleCount: session.sampleCount,
        featureCount: session.featureCount,
        recommendationCount: session.recommendationCount
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get learning session statistics
router.get('/learning/stats/:sessionId', async (req, res) => {
  try {
    if (!learningService) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    const stats = await learningService.getSessionStats(req.params.sessionId);
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Analyze current state and generate recommendations
router.post('/analyze', async (req, res) => {
  try {
    if (!addManager) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    const { telemetry, diagnostics, context, safetyLimits } = req.body;
    
    const analysis = await addManager.analyze(
      telemetry as TelemetryData,
      diagnostics as DiagnosticData,
      context as DecisionContext,
      safetyLimits as SafetyLimits
    );

    // Mark all recommendations as simulation-only in LEARN_ONLY mode
    const currentSession = learningService?.getCurrentSession();
    if (currentSession && currentSession.mode === 'LEARN_ONLY') {
      analysis.recommendations = analysis.recommendations.map(rec => ({
        ...rec,
        canApply: false,
        mode: 'SIMULATION_ONLY',
        warning: 'LEARN_ONLY mode active - recommendations are for analysis only'
      }));
    }

    res.json(analysis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Simulate a recommendation
router.post('/simulate', async (req, res) => {
  try {
    if (!addManager) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    const { recommendation } = req.body;
    
    const result = await addManager.simulateRecommendation(
      recommendation as Recommendation
    );

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Apply a recommendation (BLOCKED in LEARN_ONLY mode)
router.post('/apply', async (req, res) => {
  try {
    const currentSession = learningService?.getCurrentSession();
    
    // Block apply if in LEARN_ONLY mode
    if (currentSession && currentSession.mode === 'LEARN_ONLY') {
      return res.status(403).json({
        error: 'ECU writes are not allowed in LEARN_ONLY mode',
        code: 'WRITE_BLOCKED',
        sessionId: currentSession.sessionId
      });
    }

    // Check operator mode
    const operatorMode = req.headers['x-operator-mode'] as string;
    if (!operatorMode || operatorMode === 'DEV') {
      return res.status(403).json({
        error: 'ECU writes require WORKSHOP or LAB mode',
        code: 'MODE_RESTRICTED'
      });
    }

    // Check technician and job
    const technicianId = req.headers['x-technician-id'] as string;
    const jobId = req.headers['x-job-id'] as string;
    
    if (!technicianId || !jobId) {
      return res.status(403).json({
        error: 'ECU writes require technician and job attribution',
        code: 'ATTRIBUTION_MISSING'
      });
    }

    // In a real implementation, this would apply the recommendation
    res.status(501).json({
      error: 'Apply not implemented - use simulation instead',
      code: 'NOT_IMPLEMENTED'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Provide feedback on a recommendation
router.post('/feedback', async (req, res) => {
  try {
    if (!addManager) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    const { recommendationId, accepted, rating, notes } = req.body;
    
    await addManager.provideFeedback(
      recommendationId,
      accepted,
      rating,
      notes
    );

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get ADD metrics
router.get('/metrics', async (req, res) => {
  try {
    if (!addManager) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    const metrics = addManager.getMetrics();
    res.json(metrics);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update ADD configuration
router.put('/config', async (req, res) => {
  try {
    if (!addManager) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    // Block mode changes to ACTIVE_TUNING
    if (req.body.mode && req.body.mode !== 'LEARN_ONLY') {
      return res.status(403).json({
        error: 'Only LEARN_ONLY mode is supported',
        code: 'MODE_NOT_ALLOWED'
      });
    }

    addManager.updateConfig(req.body);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get learning statistics
router.get('/learning/stats', async (req, res) => {
  try {
    if (!addManager) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    // Access learning engine through private property (in production, add proper getter)
    const learningEngine = (addManager as any).learningEngine;
    const stats = learningEngine.getLearningStats();
    
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Reset learning data
router.post('/learning/reset', async (req, res) => {
  try {
    if (!addManager) {
      return res.status(400).json({ error: 'ADD subsystem not initialized' });
    }

    const learningEngine = (addManager as any).learningEngine;
    learningEngine.resetLearning();
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

*/

};

const router = Router(); // Dummy router for export

export default router;
