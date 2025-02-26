const mapcrontabs = function (obj) {
  // Only clone the object, don't try to format non-existent properties
  obj._data = _.clone(obj)
  return obj
}

window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  data() {
    return {
      testlogData: 'All test log content',
      fileData: 'All Logfile content', // for log file data
      output: 'Individual Job Logs',
      job_name: '', // for the create job dialog
      httpVerbs: ['GET', 'PUT', 'POST', 'DELETE'],
      selectedverb: 'GET',
      url: '',
      body: '',
      status: '',
      wallets: [],
      jobs: [],
      shortcuts: [
        '@reboot',
        '@hourly',
        '@daily',
        '@weekly',
        '@monthly',
        '@yearly'
      ],
      slots: ['minute', 'hour', 'day', 'month', 'weekday'],
      cron: {
        minute: '*',
        hour: '*',
        day: '*',
        month: '*',
        weekday: '*'
      },
      jobsTable: {
        columns: [
          {name: 'id', align: 'left', label: 'ID', field: 'id'},
          {
            name: 'name',
            align: 'left',
            label: 'Job Name',
            field: 'name'
          },
          {
            name: 'status',
            align: 'left',
            label: 'Is Running?',
            field: row => row.status ? 'Running' : 'Paused'
          },
          {
            name: 'schedule',
            align: 'left',
            label: 'Schedule',
            field: 'schedule'
          }
        ],
        pagination: {
          rowsPerPage: 10
        }
      },
      logDialog: {
        show: false
      },
      testlogDialog: {
        show: false,
        output: '',
        id: ''
      },
      id_code: '',
      jobLogDialog: {
        show: false,
        output: '',
        id: ''
      },
      jobDialog: {
        show: false,
        cron: {
          minute: '*',
          hour: '*',
          day: '*',
          month: '*',
          weekday: '*'
        },
        data: {
          selectedverb: 'GET',
          schedule: '* * * * *',
          status: 'false'
        },
        headers: []
      },
      jobStatus: {
        show: false,
        data: {}
      }
    }
  },
  computed: {
    userOptions() {
      return this.jobs.map(function (obj) {
        //console.log(obj.id)
        return {
          value: String(obj.id),
          label: String(obj.id)
        }
      })
    },
    concatenatedString() {
      // do some validation checking here for cron string
      return `${this.cron.minute} ${this.cron.hour} ${this.cron.day} ${this.cron.month} ${this.cron.weekday}`
    }
  },
  watch: {
    concatenatedString(newValue) {
      // for cron string
      this.jobDialog.data.schedule = newValue.trim()
    }
  },
  methods: {
    ///////////////Jobs////////////////////////////
    getJobs() {
      const self = this
      LNbits.api
        .request('GET', '/scheduler/api/v1/jobs', self.g.user.wallets[0].adminkey)
        .then(function(response) {
          if (response.data && response.data.data && Array.isArray(response.data.data)) {
            self.jobs = response.data.data.map(mapcrontabs)
          } else {
            console.error('Unexpected API response structure:', response)
            self.jobs = []
          }
        })
        .catch(function(error) {
          LNbits.utils.notifyApiError(error)
          self.jobs = []
        })
    },
    openLogDialog(linkId) {
      this.jobLogDialog.show = true
      const link = _.findWhere(this.jobs, {id: linkId})
      this.jobLogDialog.id = _.clone(link._data.id)
      this.id_code = this.jobLogDialog.id
    },
    openTestlogDialog(linkId) {
      this.testlogDialog.show = true
      const link = _.findWhere(this.jobs, {id: linkId})
      this.testlogDialog.id = _.clone(link._data.id)
      this.id_code = this.testlogDialog.id
    },
    fetchJobLogDialog() {
      const id = this.jobLogDialog.id
      //console.log("this.jobLogDialog.id ", this.jobLogDialog.id)
      //console.log("fetch job Log Dialog: ", id)
      LNbits.api
        .request(
          'GET',
          '/scheduler/api/v1/logentry/' + id,
          this.g.user.wallets[0].adminkey
        )
        .then(response => {
          //console.log("fetch job Log Dialog: ", id)
          //console.log(JSON.stringify(response))
          //console.log(response.status)
          this.output = response.data
          this.id_code = id
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    clearJobLogDialog() {
      this.output = ''
    },
    closeJobLogDialog() {
      this.output = '' // clears the dialog content on close
      this.jobLogDialog.show = false
    },
    openJobUpdateDialog(linkId) {
      const link = _.findWhere(this.jobs, {id: linkId})
      this.jobDialog.data = _.clone(link._data)
      if (link._data.headers === null || link._data.headers === undefined) {
        // console.log("[index] open Job Update Dialog: headers is null or undefined")
        this.jobDialog.headers = []
      } else {
        this.jobDialog.headers = _.clone(link._data.headers)
      }
      if (link._data.schedule) {
        let [minute, hour, day, month, weekday] =
          this.jobDialog.data.schedule.split(' ')
        this.cron.minute = minute
        this.cron.hour = hour
        this.cron.day = day
        this.cron.month = month
        this.cron.weekday = weekday
        //console.log("this.cron.minute", this.cron.minute)
      }

      this.jobDialog.show = true
    },
    sendJobFormData() {
      console.log(
        '[index] sendJobFormData headers: ',
        JSON.stringify(this.jobDialog.headers, null, 2)
      )
      // console.log('sendJobFormData headers: ', this.jobDialog.headers)

      const data = {
        id: this.jobDialog.data.id,
        name: this.jobDialog.data.name,
        status: this.jobDialog.data.status,
        selectedverb: this.jobDialog.data.selectedverb,
        url: this.jobDialog.data.url,
        headers: this.jobDialog.headers,
        body: this.jobDialog.data.body,
        schedule: this.jobDialog.data.schedule,
        extra: {}
      }

      if (this.jobDialog.data.id) {
        console.log('[index] sendJobFormData: update job data')
        console.log(data)
        console.log(
          '[index] sendJobFormData: headers: ',
          JSON.stringify(data.headers)
        )
        this.updateJob(data)
      } else {
        console.log('[index] sendJobFormData: create new job entry')
        console.log(data)
        this.createJob(data)
      }
    },
    displayTestJobData(job_id) {
      LNbits.api
        .request(
          'GET',
          '/scheduler/api/v1/test_log/' + job_id,
          this.g.user.wallets[0].adminkey
        )
        .then(response => {
          // Handle both string and object responses
          if (typeof response.data === 'string') {
            this.testlogData = response.data
          } else {
            // If we still get an object, format it nicely
            const job = response.data
            this.testlogData = `Test Results:
              Job Name: ${job.name}
              Status: ${job.status ? 'Active' : 'Paused'}
              Schedule: ${job.schedule}
              URL: ${job.url || 'N/A'}
              Method: ${job.selectedverb || 'N/A'}
              Headers: ${JSON.stringify(job.headers, null, 2)}
              Body: ${job.body || 'None'}`
          }
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    clearTestDialog: function () {
      // for test log data
      this.testlogDialog.show = false
      this.testlogData = ''
    },
    displayFileData() {
      // for complete log data
      LNbits.api
        .request(
          'GET',
          '/scheduler/api/v1/complete_log',
          this.g.user.wallets[0].adminkey
        )
        .then(response => {
          this.fileData = response.data
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    clearLogDialog: function () {
      // for complete log data
      this.logDialog.show = false
      // this.fileData = ''
    },
    deleteLog: function () {
      // for complete log data
      LNbits.api
        .request(
          'POST',
          '/scheduler/api/v1/delete_log',
          this.g.user.wallets[0].adminkey
        )
        .then(response => {
          if (response.status == 200) {
            this.fileData = ''
          }
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    cancelEdit: function () {
      this.jobDialog.show = false
      this.jobDialog.headers = []
      default_data = {
        selectedverb: 'GET',
        schedule: '* * * * *',
        status: 'false',
        name: '',
        url: '',
        body: ''
      }
      this.jobDialog.data = default_data
      this.cron = {
        minute: '*',
        hour: '*',
        day: '*',
        month: '*',
        weekday: '*'
      }
    },
    updateJob(data) {
      LNbits.api
        .request(
          'PUT',
          '/scheduler/api/v1/jobs/' + data.id,
          this.g.user.wallets[0].adminkey,
          data
        )
        .then(response => {
          // this.jobs.push(mapcrontabs(response.data))
          this.jobDialog.show = false
          this.jobDialog.data = {}
          this.jobDialog.headers = []
          data = {
            selectedverb: 'GET',
            schedule: '* * * * *',
            status: 'false'
          }
          this.cron = {
            minute: '*',
            hour: '*',
            day: '*',
            month: '*',
            weekday: '*'
          }

          this.getJobs()
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    createJob(data) {
      LNbits.api
        .request(
          'POST',
          '/scheduler/api/v1/jobs',
          this.g.user.wallets[0].adminkey,
          data
        )
        .then(response => {
          this.jobs.push(mapcrontabs(response.data))
          //console.log("[index] createJob response: ", response.text)
          // console.log("[index] createJob: this.jobs ", JSON.stringify(this.jobs))

          this.jobDialog.show = false
          this.jobDialog.data = {}
          this.jobDialog.headers = []
          data = {
            selectedverb: 'GET',
            schedule: '* * * * *',
            status: 'false'
          }
          this.cron = {
            minute: '*',
            hour: '*',
            day: '*',
            month: '*',
            weekday: '*'
          }
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    deleteJob(jobId) {
      LNbits.utils
        .confirmDialog('Are you sure you want to delete this Job?')
        .onOk(() => {
          LNbits.api
            .request(
              'DELETE',
              '/scheduler/api/v1/jobs/' + jobId,
              user.wallets[0].adminkey
            )
            .then(response => {
              // Refresh the jobs list from the server
              this.getJobs()
              // Use Quasar's notification system instead
              this.$q.notify({
                type: 'positive',
                message: 'Job deleted successfully'
              })
            })
            .catch(error => {
              LNbits.utils.notifyApiError(error)
            })
        })
    },
    toggleJobsStatus(id) {
      const job = this.jobs.find(job => job.id === id)
      if (job) {
        job.status = !job.status
        // Force Vue to recognize the change
        this.jobs = [...this.jobs]
        return job.status
      }
      return false
    },

    lookupJobsStatus(id) {
      const job = this.jobs.find(job => job.id === id)
      return job ? job.status : false
    },

    toggleButton(id) {
      const currentStatus = this.lookupJobsStatus(id)
      this.pauseJob(id, (!currentStatus).toString())
    },

    getButtonIcon(id) {
      const isRunning = this.lookupJobsStatus(id)
      return isRunning ? 'stop' : 'play_arrow'
    },

    updateJobStatus(jobId, newStatus) {
      const jobIndex = this.jobs.findIndex(job => job.id === jobId)
      if (jobIndex !== -1) {
        this.jobs[jobIndex].status = newStatus === 'true'
        // Force Vue to recognize the change
        this.jobs = [...this.jobs]
      }
    },

    pauseJob(jobId, status) {
      let confirm_msg = status === 'true' ? 'Are you sure you want to Start?' : 'Stopping, Are you sure?'
      const self = this

      LNbits.utils.confirmDialog(confirm_msg).onOk(() => {
        // Track that we're attempting to pause this job
        const jobIndex = this.jobs.findIndex(job => job.id === jobId)
        
        // Optimistically update UI to show desired status
        if (jobIndex !== -1) {
          // Remember original status in case we need to revert
          const originalStatus = this.jobs[jobIndex].status
          
          // Optimistically update to new status
          this.updateJobStatus(jobId, status)
        }
        
        LNbits.api
          .request(
            'POST',
            '/scheduler/api/v1/pause/' + jobId + '/' + status,
            self.g.user.wallets[0].adminkey
          )
          .then(function(response) {
            console.log('Job status updated successfully')
            
            // Always refresh the jobs list to ensure UI is in sync with server
            setTimeout(function() {
              self.getJobs()
            }, 500)
          })
          .catch(function(error) {
            console.error('API error:', error)
            
            // Show error notification
            LNbits.utils.notifyApiError(error)
            
            // Still refresh the jobs list to get accurate state from server
            setTimeout(function() {
              self.getJobs()
            }, 500)
          })
      })
    },

    getButtonColor(id) {
      const lookup_state = this.lookupJobsStatus(id)
      return lookup_state ? 'red' : 'green'
    },

    getButtonText(id) {
      const lookup_state = this.lookupJobsStatus(id)
      return lookup_state ? 'Stop' : 'Play'
    },
    flattenExportCSV(columns, data, fileName) {
      const flattenNestedData = function (data, field) {
        if (typeof field === 'function') {
          return field(data)
        } else if (field === 'headers') {
          return JSON.stringify(data['headers'])
        } else if (field === 'body') {
          return JSON.stringify(data['body'])
        } else if (typeof field === 'object') {
          return Object.keys(field)
            .map(key => `${key}: ${field[key]}`)
            .join(', ')
        } else {
          return field.split('.').reduce((obj, key) => obj[key], data)
        }
      }

      const wrapCsvValue = function (val, formatFn) {
        const formatted = formatFn !== void 0 ? formatFn(val) : val

        formatted =
          formatted === void 0 || formatted === null ? '' : String(formatted)

        formatted = formatted.split('"').join('""')

        return `"${formatted}"`
      }

      const content = [
        columns.map(function (col) {
          return wrapCsvValue(col.label)
        })
      ]
        .concat(
          data.map(function (row) {
            return columns
              .map(function (col) {
                const fieldValue = flattenNestedData(row, col.field)
                return wrapCsvValue(fieldValue, col.format)
              })
              .join(',')
          })
        )
        .join('\r\n')

      const status = Quasar.utils.exportFile(
        `${fileName || 'table-export'}.csv`,
        content,
        'text/csv'
      )

      if (status !== true) {
        Quasar.plugins.Notify.create({
          message: 'Browser denied file download...',
          color: 'negative',
          icon: null
        })
      }
    },
    exportJobsCSV() {
      //LNbits.utils.exportCSV(this.jobsTable.columns, this.jobs)
      LNbits.api
        .request(
          'GET',
          '/scheduler/api/v1/jobs',
          this.g.user.wallets[0].adminkey
        )
        .then(response => {
          if (response.status == 200) {
            let data = response.data
            // Dynamically generate columns based on keys in the data
            let columns = Object.keys(data[0]).map(key => ({
              label: key.charAt(0).toUpperCase() + key.slice(1),
              field: key
            }))
            this.flattenExportCSV(columns, data, 'scheduler-export')
          }
        })
        .catch(LNbits.utils.notifyApiError)
    }
  },
  props: {
    row: {
      type: Object,
      default: () => ({id: null}) // Define a default row object if none is provided
    }
  },
  created() {
    if (this.g.user.wallets.length) {
      this.getJobs()
    }
  }
})
