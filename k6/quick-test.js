import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const authTokenTrend = new Trend('auth_token_time');
const itemCreationTrend = new Trend('item_creation_time');

// Quick test configuration - only 1 minute
export const options = {
  stages: [
    // Ramp up to 5 users over 15 seconds
    { duration: '15s', target: 5 },
    // Stay at 5 users for 30 seconds
    { duration: '30s', target: 5 },
    // Ramp down to 0 users over 15 seconds
    { duration: '15s', target: 0 },
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
  username: 'quicktest',
  password: 'quicktest123',
  email: 'quicktest@example.com',
};

// Helper function to get auth token
function getAuthToken() {
  const loginData = `username=${TEST_USER.username}&password=${TEST_USER.password}`;
  
  const startTime = new Date();
  const response = http.post(`${BASE_URL}/api/v1/auth/token`, loginData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
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
    full_name: 'Quick Test User',
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
  const getItems = check(http.get(`${BASE_URL}/api/v1/items/?skip=0&limit=5`, { headers }), {
    'get items status is 200': (r) => r.status === 200,
    'get items response time < 300ms': (r) => r.timings.duration < 300,
    'get items returns items array': (r) => r.json('items') !== undefined,
  });
  
  if (!getItems) {
    errorRate.add(1);
  }
  
  // Test 3: Create item (write operation)
  const itemData = {
    title: `Quick Test Item ${Date.now()}`,
    description: 'Created during quick test',
    price: Math.floor(Math.random() * 100) + 10,
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
  
  // Shorter sleep for quick test
  sleep(Math.random() * 1 + 0.5); // Sleep between 0.5-1.5 seconds
}

// Setup function to create test user
export function setup() {
  console.log('Setting up quick test...');
  createTestUser();
  console.log('Quick test setup complete');
}

// Teardown function
export function teardown(data) {
  console.log('Quick test completed');
} 