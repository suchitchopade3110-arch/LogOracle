// src/app.js — boot order matters.

async function start() {
  const { loadFromVault } = require('./config/secrets');
  if (process.env.VAULT_ADDR) {
    try {
      await loadFromVault();
    } catch (err) {
      if (process.env.VAULT_REQUIRED === 'true') throw err;
      console.warn('[VAULT] unavailable, falling back to env:', err.message);
    }
  }

  const express = require('express');
  const { inputSanitize } = require('./middleware/inputSanitize');
  const { apiLimiter } = require('./middleware/rateLimit');
  const { plantHoneytokens } = require('./db/honeytoken');

  const app = express();
  app.set('trust proxy', 1);
  app.use(express.json());
  app.use(inputSanitize);
  app.use(apiLimiter);

  app.get('/health', (_req, res) => res.json({ status: 'ok' }));

  await plantHoneytokens();

  app.listen(3000, () => console.log('[APP] ready'));
}

start().catch((err) => {
  console.error(err);
  process.exit(1);
});
