import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Stress test configuration
export const options = {
  stages: [
    // Ramp up to 20 users over 1 minute
    { duration: '1m', target: 20 },
    // Stay at 20 users for 2 minutes
    { duration: '2m', target: 20 },
    // Ramp up to 100 users over 2 minutes
    { duration: '2m', target: 100 },
    // Stay at 100 users for 3 minutes
    { duration: '3m', target: 100 },
    // Ramp up to 200 users over 2 minutes
    { duration: '2m', target: 200 },
    // Stay at 200 users for 3 minutes
    { duration: '3m', target: 200 },
    // Ramp down to 0 users over 1 minute
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests should be below 1s
    http_req_failed: ['rate<0.2'],     // Error rate should be below 20%
    errors: ['rate<0.2'],              // Custom error rate should be below 20%
  },
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USERS = [
  { username: 'stress1', password: 'stress123', email: 'stress1@example.com' },
  { username: 'stress2', password: 'stress123', email: 'stress2@example.com' },
  { username: 'stress3', password: 'stress123', email: 'stress3@example.com' },
  { username: 'stress4', password: 'stress123', email: 'stress4@example.com' },
  { username: 'stress5', password: 'stress123', email: 'stress5@example.com' },
];

// Helper function to get auth token
function getAuthToken(userIndex) {
  const user = TEST_USERS[userIndex % TEST_USERS.length];
  const loginData = `username=${user.username}&password=${user.password}`;
  
  const response = http.post(`${BASE_URL}/api/v1/auth/token`, loginData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  
  if (response.status === 200) {
    return response.json('access_token');
  }
  return null;
}

// Helper function to create test users
function createTestUsers() {
  TEST_USERS.forEach(user => {
    const userData = {
      email: user.email,
      username: user.username,
      password: user.password,
      full_name: `Stress Test User ${user.username}`,
    };
    
    http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify(userData), {
      headers: { 'Content-Type': 'application/json' },
    });
  });
}

// Main test function
export default function () {
  const userIndex = Math.floor(Math.random() * TEST_USERS.length);
  const token = getAuthToken(userIndex);
  
  if (!token) {
    errorRate.add(1);
    return;
  }
  
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  
  // Test 1: Health check (lightweight)
  const healthCheck = check(http.get(`${BASE_URL}/health`), {
    'health check status is 200': (r) => r.status === 200,
  });
  
  if (!healthCheck) {
    errorRate.add(1);
  }
  
  // Test 2: Get items (read operation)
  const getItems = check(http.get(`${BASE_URL}/api/v1/items/?skip=0&limit=5`, { headers }), {
    'get items status is 200': (r) => r.status === 200,
  });
  
  if (!getItems) {
    errorRate.add(1);
  }
  
  // Test 3: Create item (write operation) - more intensive
  const itemData = {
    title: `Stress Test Item ${Date.now()}-${Math.random()}`,
    description: 'Created during stress test',
    price: Math.floor(Math.random() * 1000) + 100,
  };
  
  const createItem = check(http.post(`${BASE_URL}/api/v1/items/`, JSON.stringify(itemData), { headers }), {
    'create item status is 201': (r) => r.status === 201,
  });
  
  if (!createItem) {
    errorRate.add(1);
  }
  
  // Test 4: Get current user
  const getCurrentUser = check(http.get(`${BASE_URL}/api/v1/auth/me`, { headers }), {
    'get current user status is 200': (r) => r.status === 200,
  });
  
  if (!getCurrentUser) {
    errorRate.add(1);
  }
  
  // Shorter sleep for stress test
  sleep(Math.random() * 0.5 + 0.1); // Sleep between 0.1-0.6 seconds
}

// Setup function
export function setup() {
  console.log('Setting up stress test...');
  createTestUsers();
  console.log('Stress test setup complete');
}

// Teardown function
export function teardown(data) {
  console.log('Stress test completed');
} 