<template>
  <v-container fluid class="pa-0">
    <v-parallax
      src="https://cdn.vuetifyjs.com/images/backgrounds/vbanner.jpg"
      height="200"
    >
      <v-row align="center" justify="center">
        <v-col cols="12" class="text-center">
          <h1 class="text-h3 font-weight-bold white--text mb-4">Document Search Agent</h1>
          <p class="text-h6 white--text">Intelligent document search powered by AI</p>
        </v-col>
      </v-row>
    </v-parallax>

    <v-container>
      <v-card class="mx-auto main-card" elevation="3" rounded="lg">
        <v-card-text>
          <!-- Status Text -->
          <v-slide-y-transition>
            <v-alert
              :type="statusType"
              v-if="statusText"
              class="mb-6"
              dense
              border="left"
              elevation="2"
            >
              {{ statusText }}
            </v-alert>
          </v-slide-y-transition>

          <!-- Search Section -->
          <v-card class="search-card mb-6" outlined>
            <v-card-text>
              <!-- Controls Row -->
              <v-row>
                <v-col cols="12" sm="4">
                  <v-select
                    v-model="selectedProvider"
                    :items="availableProviders"
                    label="AI Provider"
                    dense
                    outlined
                    hide-details
                    class="rounded-lg"
                    prepend-inner-icon="mdi-robot"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="maxIterations"
                    label="Max Iterations"
                    type="number"
                    dense
                    outlined
                    hide-details
                    class="rounded-lg"
                    prepend-inner-icon="mdi-repeat"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="resultsPerSearch"
                    label="Results Per Search"
                    type="number"
                    dense
                    outlined
                    hide-details
                    class="rounded-lg"
                    prepend-inner-icon="mdi-format-list-numbered"
                  ></v-text-field>
                </v-col>
              </v-row>

              <!-- Search Field -->
              <v-text-field
                v-model="searchQuery"
                label="What would you like to search for?"
                outlined
                :loading="isSearching"
                :disabled="isSearching"
                @keyup.enter="performSearch"
                append-icon="mdi-magnify"
                @click:append="performSearch"
                class="mt-6 search-input rounded-lg"
                hide-details
                clearable
                placeholder="Enter your search query here..."
              ></v-text-field>
            </v-card-text>
          </v-card>

          <!-- Results Section -->
          <v-expand-transition>
            <div v-if="searchSteps.length > 0">
              <!-- Steps Timeline -->
              <v-timeline dense class="mt-6">
                <v-timeline-item
                  v-for="(step, index) in searchSteps"
                  :key="index"
                  :color="getStepColor(step)"
                  small
                >
                  <v-card class="timeline-card" elevation="2">
                    <v-card-title class="text-subtitle-1 font-weight-bold pb-1">
                      {{ step.action }}
                    </v-card-title>
                    <v-divider></v-divider>
                    <v-card-text class="pt-3">
                      <p class="text-body-2">{{ step.description }}</p>
                      
                      <!-- Results Display -->
                      <v-expansion-panels flat v-if="step.results && step.results.length">
                        <v-expansion-panel>
                          <v-expansion-panel-header class="primary--text">
                            {{ step.results.length }} Results Found
                          </v-expansion-panel-header>
                          <v-expansion-panel-content>
                            <v-list two-line>
                              <div v-for="(result, rIndex) in step.results" :key="rIndex">
                                <v-list-item>
                                  <v-list-item-content>
                                    <v-list-item-title v-if="result.type === 'document'" class="d-flex align-center justify-space-between">
                                      <span>{{ result.content.title }}</span>
                                      <v-chip small color="primary" text-color="white">
                                        Score: {{ result.content.score.toFixed(2) }}
                                      </v-chip>
                                    </v-list-item-title>
                                    <v-list-item-subtitle v-if="result.type === 'document'">
                                      <div class="mt-2 pa-3 rounded-lg highlight-text">
                                        {{ result.content.highlights[0] }}
                                      </div>
                                    </v-list-item-subtitle>
                                    <v-list-item-subtitle v-else class="text-body-2">
                                      {{ result.content }}
                                    </v-list-item-subtitle>
                                  </v-list-item-content>
                                </v-list-item>
                                <v-divider v-if="rIndex < step.results.length - 1"></v-divider>
                              </div>
                            </v-list>
                          </v-expansion-panel-content>
                        </v-expansion-panel>
                      </v-expansion-panels>
                    </v-card-text>
                  </v-card>
                </v-timeline-item>
              </v-timeline>

              <!-- Final Answer -->
              <v-slide-y-transition>
                <v-card v-if="finalAnswer" class="mt-6 final-answer-card" elevation="3">
                  <v-card-title class="text-h5 primary--text">
                    <v-icon left color="primary">mdi-check-circle</v-icon>
                    Final Answer
                  </v-card-title>
                  <v-card-text>
                    <div class="pa-4 rounded-lg answer-text">
                      {{ finalAnswer.answer }}
                    </div>

                    <!-- Sources -->
                    <v-expansion-panels v-if="finalAnswer.sources" class="mt-4" flat>
                      <v-expansion-panel>
                        <v-expansion-panel-header class="primary--text">
                          <v-icon left color="primary">mdi-book-open-variant</v-icon>
                          Source Documents
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                          <v-list>
                            <div v-for="(source, index) in finalAnswer.sources" :key="index">
                              <v-list-item>
                                <v-list-item-content>
                                  <v-list-item-title class="d-flex align-center justify-space-between">
                                    <span>{{ source.title }}</span>
                                    <v-chip small color="primary" text-color="white">
                                      Score: {{ source.score.toFixed(2) }}
                                    </v-chip>
                                  </v-list-item-title>
                                  <v-list-item-subtitle>
                                    <div v-for="(highlight, hIndex) in source.highlights" 
                                         :key="hIndex"
                                         class="mt-2 pa-3 rounded-lg highlight-text">
                                      {{ highlight }}
                                    </div>
                                  </v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>
                              <v-divider v-if="index < finalAnswer.sources.length - 1"></v-divider>
                            </div>
                          </v-list>
                        </v-expansion-panel-content>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-card-text>
                </v-card>
              </v-slide-y-transition>
            </div>
          </v-expand-transition>
        </v-card-text>
      </v-card>
    </v-container>
  </v-container>
</template>

<script>
export default {
  data()  {
    return {
      searchQuery: '',
      statusText: 'Ready to search',
      statusType: 'info',
      isSearching: false,
      searchSteps: [],
      finalAnswer: null,
      selectedProvider: 'Gemini',
      availableProviders: ['Gemini'],
      maxIterations: 3,
      resultsPerSearch: 5
    }
  },
  methods: {
    async performSearch() {
      if (!this.searchQuery.trim()) return

      this.isSearching = true
      this.searchSteps = []
      this.finalAnswer = null
      this.statusText = 'Searching...'
      this.statusType = 'info'

      try {
        const response = await this.$axios.$post('/api/search', {
          query: this.searchQuery,
          numResults: parseInt(this.resultsPerSearch),
          maxIterations: parseInt(this.maxIterations)
        })

        if (response.success) {
          this.searchSteps = response.results.steps || []
          this.finalAnswer = response.results.finalResult
          this.statusText = 'Search completed successfully!'
          this.statusType = 'success'
        } else {
          this.statusText = response.message
          this.statusType = 'error'
        }
      } catch (error) {
        this.statusText = error.response?.data?.message || 'Search failed'
        this.statusType = 'error'
      } finally {
        this.isSearching = false
      }
    },
    getStepColor(step) {
      if (step.results && step.results.some(r => r.type === 'evaluation' && r.content.status === 'accepted')) {
        return 'success'
      }
      return 'primary'
    }
  }
}
</script>

<style scoped>
.main-card {
  margin-top: -50px;
  border-radius: 16px !important;
}

.search-card {
  background-color: #f8f9fa !important;
  border-radius: 12px !important;
}

.search-input {
  font-size: 1.1rem;
}

.timeline-card {
  border-radius: 12px !important;
}

.highlight-text {
  background-color: #f8f9fa;
  border-left: 4px solid var(--v-primary-base);
  font-size: 0.95rem;
}

.answer-text {
  background-color: #f8f9fa;
  border-left: 4px solid var(--v-primary-base);
  font-size: 1rem;
  line-height: 1.6;
}

.final-answer-card {
  border-radius: 16px !important;
}

.v-timeline-item__body {
  max-width: 100% !important;
}

/* Smooth transitions */
.v-enter-active, .v-leave-active {
  transition: opacity 0.3s ease;
}

.v-enter, .v-leave-to {
  opacity: 0;
}
</style>
