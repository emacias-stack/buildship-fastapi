import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Spike test configuration
export const options = {
  stages: [
    // Normal load: 10 users for 1 minute
    { duration: '1m', target: 10 },
    // Spike: 100 users for 30 seconds
    { duration: '30s', target: 100 },
    // Back to normal: 10 users for 1 minute
    { duration: '1m', target: 10 },
    // Another spike: 150 users for 30 seconds
    { duration: '30s', target: 150 },
    // Back to normal: 10 users for 1 minute
    { duration: '1m', target: 10 },
    // Final spike: 200 users for 30 seconds
    { duration: '30s', target: 200 },
    // Ramp down: 0 users over 30 seconds
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<800'], // 95% of requests should be below 800ms
    http_req_failed: ['rate<0.15'],   // Error rate should be below 15%
    errors: ['rate<0.15'],            // Custom error rate should be below 15%
  },
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USERS = [
  { username: 'spike1', password: 'spike123', email: 'spike1@example.com' },
  { username: 'spike2', password: 'spike123', email: 'spike2@example.com' },
  { username: 'spike3', password: 'spike123', email: 'spike3@example.com' },
  { username: 'spike4', password: 'spike123', email: 'spike4@example.com' },
  { username: 'spike5', password: 'spike123', email: 'spike5@example.com' },
  { username: 'spike6', password: 'spike123', email: 'spike6@example.com' },
  { username: 'spike7', password: 'spike123', email: 'spike7@example.com' },
  { username: 'spike8', password: 'spike123', email: 'spike8@example.com' },
  { username: 'spike9', password: 'spike123', email: 'spike9@example.com' },
  { username: 'spike10', password: 'spike123', email: 'spike10@example.com' },
];

// Helper function to get auth token
function getAuthToken(userIndex) {
  const user = TEST_USERS[userIndex % TEST_USERS.length];
  const loginData = {
    username: user.username,
    password: user.password,
  };
  
  const response = http.post(`${BASE_URL}/api/v1/auth/token`, loginData);
  
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
      full_name: `Spike Test User ${user.username}`,
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
  
  // Test 1: Health check (fastest)
  const healthCheck = check(http.get(`${BASE_URL}/health`), {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 300ms': (r) => r.timings.duration < 300,
  });
  
  if (!healthCheck) {
    errorRate.add(1);
  }
  
  // Test 2: Get items (read operation)
  const getItems = check(http.get(`${BASE_URL}/api/v1/items/?skip=0&limit=3`, { headers }), {
    'get items status is 200': (r) => r.status === 200,
    'get items response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  if (!getItems) {
    errorRate.add(1);
  }
  
  // Test 3: Create item (write operation)
  const itemData = {
    title: `Spike Test Item ${Date.now()}-${Math.random()}`,
    description: 'Created during spike test',
    price: Math.floor(Math.random() * 1000) + 100,
  };
  
  const createItem = check(http.post(`${BASE_URL}/api/v1/items/`, JSON.stringify(itemData), { headers }), {
    'create item status is 201': (r) => r.status === 201,
    'create item response time < 800ms': (r) => r.timings.duration < 800,
  });
  
  if (!createItem) {
    errorRate.add(1);
  }
  
  // Test 4: Get current user
  const getCurrentUser = check(http.get(`${BASE_URL}/api/v1/auth/me`, { headers }), {
    'get current user status is 200': (r) => r.status === 200,
    'get current user response time < 300ms': (r) => r.timings.duration < 300,
  });
  
  if (!getCurrentUser) {
    errorRate.add(1);
  }
  
  // Very short sleep for spike test
  sleep(Math.random() * 0.3 + 0.05); // Sleep between 0.05-0.35 seconds
}

// Setup function
export function setup() {
  console.log('Setting up spike test...');
  createTestUsers();
  console.log('Spike test setup complete');
}

// Teardown function
export function teardown(data) {
  console.log('Spike test completed');
} 