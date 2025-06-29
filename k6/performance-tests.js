import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const authTokenTrend = new Trend('auth_token_time');
const itemCreationTrend = new Trend('item_creation_time');

// Test configuration
export const options = {
  stages: [
    // Ramp up to 10 users over 30 seconds
    { duration: '30s', target: 10 },
    // Stay at 10 users for 1 minute
    { duration: '1m', target: 10 },
    // Ramp up to 50 users over 30 seconds
    { duration: '30s', target: 50 },
    // Stay at 50 users for 2 minutes
    { duration: '2m', target: 50 },
    // Ramp down to 0 users over 30 seconds
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.1'],    // Error rate should be below 10%
    errors: ['rate<0.1'],             // Custom error rate should be below 10%
  },
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USER = {
  username: 'perftest',
  password: 'perftest123',
  email: 'perftest@example.com',
};

// Helper function to get auth token
function getAuthToken() {
  const loginData = {
    username: TEST_USER.username,
    password: TEST_USER.password,
  };
  
  const startTime = new Date();
  const response = http.post(`${BASE_URL}/api/v1/auth/token`, loginData);
  const endTime = new Date();
  
  authTokenTrend.add(endTime - startTime);
  
  if (response.status === 200) {
    return response.json('access_token');
  }
  return null;
}

// Helper function to create test user if not exists
function createTestUser() {
  const userData = {
    email: TEST_USER.email,
    username: TEST_USER.username,
    password: TEST_USER.password,
    full_name: 'Performance Test User',
  };
  
  const response = http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify(userData), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  return response.status === 201 || response.status === 400; // 400 means user already exists
}

// Main test function
export default function () {
  const token = getAuthToken();
  
  if (!token) {
    errorRate.add(1);
    return;
  }
  
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  
  // Test 1: Health check
  const healthCheck = check(http.get(`${BASE_URL}/health`), {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  if (!healthCheck) {
    errorRate.add(1);
  }
  
  // Test 2: Get items (read operation)
  const getItems = check(http.get(`${BASE_URL}/api/v1/items/?skip=0&limit=10`, { headers }), {
    'get items status is 200': (r) => r.status === 200,
    'get items response time < 300ms': (r) => r.timings.duration < 300,
    'get items returns items array': (r) => r.json('items') !== undefined,
  });
  
  if (!getItems) {
    errorRate.add(1);
  }
  
  // Test 3: Create item (write operation)
  const itemData = {
    title: `Performance Test Item ${Date.now()}`,
    description: 'Created during performance test',
    price: Math.floor(Math.random() * 1000) + 100,
  };
  
  const startTime = new Date();
  const createItem = check(http.post(`${BASE_URL}/api/v1/items/`, JSON.stringify(itemData), { headers }), {
    'create item status is 201': (r) => r.status === 201,
    'create item response time < 500ms': (r) => r.timings.duration < 500,
    'create item returns item with id': (r) => r.json('id') !== undefined,
  });
  const endTime = new Date();
  
  itemCreationTrend.add(endTime - startTime);
  
  if (!createItem) {
    errorRate.add(1);
  }
  
  // Test 4: Get current user
  const getCurrentUser = check(http.get(`${BASE_URL}/api/v1/auth/me`, { headers }), {
    'get current user status is 200': (r) => r.status === 200,
    'get current user response time < 200ms': (r) => r.timings.duration < 200,
    'get current user returns user data': (r) => r.json('username') === TEST_USER.username,
  });
  
  if (!getCurrentUser) {
    errorRate.add(1);
  }
  
  // Random sleep between requests to simulate real user behavior
  sleep(Math.random() * 2 + 1); // Sleep between 1-3 seconds
}

// Setup function to create test user
export function setup() {
  console.log('Setting up performance test...');
  createTestUser();
  console.log('Performance test setup complete');
}

// Teardown function
export function teardown(data) {
  console.log('Performance test completed');
} 