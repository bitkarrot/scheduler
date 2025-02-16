const mapcrontabs = function (obj) {
  obj.date = Quasar.date.formatDate(new Date(obj.time), 'YYYY-MM-DD HH:mm')
  obj.fsat = new Intl.NumberFormat(LOCALE).format(obj.amount)
  obj.walllink = ['../wallet?usr=', obj.user, '&wal=', obj.id].join('')
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
            field: 'status'
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
    getJobs: () => {
      LNbits.api
        .request(
          'GET',
          '/scheduler/api/v1/jobs',
          user.wallets[0].adminkey
        )
        .then(response => {
          this.jobs = response.data.data.map(function (obj) {
            return mapcrontabs(obj)
          })
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
      // for test log data
      // console.log("job id: ", job_id)
      LNbits.api
        .request(
          'GET',
          '/scheduler/api/v1/test_log/' + job_id,
          this.g.user.wallets[0].adminkey
        )
        .then(response => {
          //console.log("response.data: ", response.data)
          this.testlogData = response.data
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
        .onOk(function () {
          LNbits.api
            .request(
              'DELETE',
              '/scheduler/api/v1/jobs/' + jobId,
              this.g.user.wallets[0].adminkey
            )
            .then(response => {
              this.jobs = _.reject(this.jobs, function (obj) {
                return obj.id == jobId
              })
            })
            .catch(function (error) {
              LNbits.utils.notifyApiError(error)
            })
        })
    },
    toggleJobsStatus(id) {
      for (let i = 0; i < this.jobs.length; i++) {
        if (this.jobs[i].id === id) {
          const newstatus = this.jobs[i].status
          if (newstatus === true) {
            this.jobs[i].status = false
          } else {
            this.jobs[i].status = true
          }
          console.log(
            'jobs id: ',
            this.jobs[i].id,
            'status:',
            this.jobs[i].status
          )
          //break; // Stop the loop once the target object is found
          return this.jobs[i].status
        }
      }
    },
    lookupJobsStatus(id) {
      for (let i = 0; i < this.jobs.length; i++) {
        if (this.jobs[i].id === id) {
          return this.jobs[i].status
        }
      }
    },
    toggleButton(id) {
      const lookup_state = this.lookupJobsStatus(id)
      //console.log("lookup: ", lookup_state)
      //console.log("opposite: ", !lookup_state)
      const result = this.pauseJob(id, !lookup_state)
      //console.log("result: ", result)
    },
    getButtonIcon(id) {
      const lookup_state = this.lookupJobsStatus(id)
      return lookup_state ? 'stop' : 'play_arrow'
    },
    getButtonText(id) {
      const lookup_state = this.lookupJobsStatus(id)
      return lookup_state ? 'Stop' : 'Play'
    },
    getButtonColor(id) {
      const lookup_state = this.lookupJobsStatus(id)
      return lookup_state ? 'red' : 'green'
    },
    pauseJob(jobId, status) {
      let confirm_msg = 'Stopping, Are you sure?' // stop
      if (status) {
        confirm_msg = 'Are you sure you want to Start?'
      }
      LNbits.utils.confirmDialog(confirm_msg).onOk(function () {
        LNbits.api
          .request(
            'POST',
            '/scheduler/api/v1/pause/' + jobId + '/' + status,
            this.g.user.wallets[0].adminkey
          )
          .then(response => {
            //console.log("Pause Response status", response.status);
            const toggle_state = this.toggleJobsStatus(jobId)
          })
          .catch(function (error) {
            LNbits.utils.notifyApiError(error)
          })
      })
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
