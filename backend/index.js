require('dotenv').config();
const express = require('express');
const session = require('express-session');
const Keycloak = require('keycloak-connect');
const cors = require('cors');

const PORT = process.env.PORT || 8000;

const app = express();

app.use(cors());

const memoryStore = new session.MemoryStore();

const keycloak = new Keycloak(
  { store: memoryStore },
  {
    realm: "reports-realm",
    clientId: "reports-api",
    bearerOnly: true,
    serverUrl: process.env.KEYCLOAK_URL || "http://keycloak:8080/",
    credentials: {
      secret: process.env.KEYCLOAK_SECRET,
    },
  }
);

app.use(
  session({
    secret: 'zero',
    resave: false,
    saveUninitialized: true,
    store: memoryStore,
  })
);

app.use(keycloak.middleware());

app.get('/reports', keycloak.protect('realm:prothetic_user'), (req, res) => {
  res.json({
    reports: [
      { id: 1, title: '1 Report', data: 'Some text' },
      { id: 2, title: '2 Report', data: 'Some text' },
      { id: 3, title: '3 Report', data: 'Some text' },
      { id: 4, title: '4 Report', data: 'Some text' },
      { id: 5, title: '5 Report', data: 'Some text' },
    ]
  });
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
