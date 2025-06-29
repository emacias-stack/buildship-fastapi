// k6 configuration file
export const config = {
  // Common configuration
  common: {
    // Base URL for the application
    baseUrl: __ENV.BASE_URL || 'http://localhost:8000',
    
    // Default thresholds
    thresholds: {
      http_req_duration: ['p(95)<500'],
      http_req_failed: ['rate<0.1'],
    },
    
    // Default stages for load testing
    stages: [
      { duration: '30s', target: 10 },
      { duration: '1m', target: 10 },
      { duration: '30s', target: 50 },
      { duration: '2m', target: 50 },
      { duration: '30s', target: 0 },
    ],
  },
  
  // Development environment
  development: {
    baseUrl: 'http://localhost:8000',
    thresholds: {
      http_req_duration: ['p(95)<1000'],
      http_req_failed: ['rate<0.2'],
    },
  },
  
  // Staging environment
  staging: {
    baseUrl: 'https://staging-api.buildship.com',
    thresholds: {
      http_req_duration: ['p(95)<500'],
      http_req_failed: ['rate<0.1'],
    },
  },
  
  // Production environment
  production: {
    baseUrl: 'https://api.buildship.com',
    thresholds: {
      http_req_duration: ['p(95)<300'],
      http_req_failed: ['rate<0.05'],
    },
  },
};

// Helper function to get configuration for environment
export function getConfig(environment = 'development') {
  return {
    ...config.common,
    ...config[environment],
  };
}

// Export default configuration
export default config; 