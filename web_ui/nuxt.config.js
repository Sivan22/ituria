export default {
  head: {
    title: 'Document Search',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' }
    ]
  },
  modules: [
    '@nuxtjs/axios',
  ],
  buildModules: [
    '@nuxtjs/vuetify',
  ],
  axios: {
    baseURL: 'http://localhost:3001'
  },
  vuetify: {
    theme: {
      themes: {
        light: {
          primary: '#2563eb',    // Modern blue
          secondary: '#64748b',  // Slate
          accent: '#3b82f6',     // Bright blue
          error: '#ef4444',      // Modern red
          info: '#3b82f6',       // Info blue
          success: '#22c55e',    // Modern green
          warning: '#f59e0b',    // Modern amber
          background: '#f8fafc'  // Light gray background
        }
      },
      options: {
        customProperties: true
      }
    },
    defaultAssets: {
      font: {
        family: 'Inter'
      }
    }
  }
}
