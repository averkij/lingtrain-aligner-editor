<template>
  <div>
    <div class="text-h4 mt-10 font-weight-bold">
      <v-icon color="blue" large>mdi-pencil</v-icon> Alignments
    </div>

    <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2"
      v-if="!itemsProcessing || !itemsProcessing[langCodeFrom] || (itemsProcessing[langCodeFrom].length == 0)">
      There are no previously aligned documents yet.
    </v-alert>
    <div v-else class="mt-5">

      <div class="text-h5 mt-10 font-weight-bold">Alignments</div>
      <v-card class="mt-6">
        <div class="green lighten-5" dark>
          <v-card-title>Alignments</v-card-title>
          <v-card-text>List of previosly aligned documents [{{langCodeFrom}}-{{langCodeTo}}]</v-card-text>
          <!-- {{itemsProcessing}} -->
        </div>
        <v-divider/>
        <v-list flat class="pa-0">
          <v-list-item-group mandatory v-model="selectedListItem">
            <v-list-item v-for="(item, i) in itemsProcessing[langCodeFrom]" :key="i"
              @change="selectProcessing(item, item.guid)"
              @mouseover="hoverAlignmentIndex = i"
              @mouseleave="hoverAlignmentIndex = -1">
              <v-list-item-icon>
                <v-icon v-if="item.state[0]==PROC_INIT || item.state[0]==PROC_IN_PROGRESS" color="blue">
                  mdi-clock-outline</v-icon>
                <v-icon v-else-if="item.state[0]==PROC_ERROR" color="error">mdi-alert-circle</v-icon>
                <v-icon v-else-if="item.state[0]==PROC_IN_PROGRESS_DONE" color="blue">mdi-check</v-icon>
                <v-icon v-else color="green">mdi-check-circle-outline</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>{{item.name}}<v-chip class="ml-4" color="grey" text-color="black" small outlined>
                    {{item.state[2]}} / {{item.state[1]}}</v-chip>
                </v-list-item-title>
              </v-list-item-content>
              <v-icon v-show="hoverAlignmentIndex == i" class="ml-2" @click.stop.prevent="hoveredAlignmentItem=item, showConfirmDeleteAlignmentDialog=true">mdi-close</v-icon>
              <!-- progress bar -->
              <v-progress-linear stream buffer-value="0" :value="item.state[2]/item.state[1] * 100" color="green"
                :active="item.state[0]==PROC_INIT || item.state[0]==PROC_IN_PROGRESS" absolute bottom>
              </v-progress-linear>
            </v-list-item>
          </v-list-item-group>
        </v-list>
        <ConfirmDeleteDialog v-model="showConfirmDeleteAlignmentDialog"
          :itemName=hoveredAlignmentItem.name
          @confirmDelete="performDeleteAlignment" />
      </v-card>

      <!-- PROCESSING DOCUMENTS LIST BLOCK -->
      <div class="text-h5 mt-12 font-weight-bold">
        {{selectedProcessing.name}}
      </div>

      <div class="text-h4 mt-10 font-weight-bold">
        <v-icon color="blue" large>mdi-cloud-download</v-icon> Corpora
      </div>

      <v-alert v-if="!processing || !processing.items || processing.items.length == 0" type="info" border="left"
        colored-border color="info" class="mt-6" elevation="2">
        Please, wait. Alignment is in progress.
      </v-alert>
      <div v-else>
        <!-- <div class="mt-10">
          <v-row>
            <v-col cols="12">
              <v-subheader class="pl-0">Similarity threshold: {{thresholdText}}</v-subheader>
              <v-slider v-model="downloadThreshold" thumb-label :thumb-size="24">
                <template v-slot:thumb-label="{ value }">
                  {{ satisfactionEmojis[Math.min(Math.floor(value / 10), 9)] }}
                </template>
              </v-slider>
            </v-col>
          </v-row>
          <div class="text-center">
            <v-progress-circular :rotate="360" :size="260" :width="15" :value="corporaSizeRelative" color="teal">
              <div class="text-h2 black--text mt-4" style="line-height:2rem !important;">{{corporaSizeAbsolute}} <br />
                <span class="text-h5 grey--text">sentences</span></div>
            </v-progress-circular>
          </div>
        </div> -->
        <div class="mt-10">
          <v-row>
            <v-col cols="12" sm="6">
              <DownloadPanel @downloadFile="downloadProcessing" :info="LANGUAGES[langCodeFrom]" :isLoading=isLoading
                :count=100 :countOrig=splitted[langCodeFrom].meta.lines_count>
              </DownloadPanel>
            </v-col>
            <v-col cols="12" sm="6">
              <DownloadPanel @downloadFile="downloadProcessing" :info="LANGUAGES[langCodeTo]" :isLoading=isLoading
                :count=100 :countOrig=splitted[langCodeTo].meta.lines_count>
              </DownloadPanel>
            </v-col>
          </v-row>
        </div>
        <div class="text-h5 mt-10 font-weight-bold">Corpora in TMX format</div>
        <v-btn class="primary mt-5" @click="downloadProcessingTmx()"><v-icon left color="white">mdi-download</v-icon>Download</v-btn>
      </div>
    </div>
  </div>
</template>

<script>
  import DownloadPanel from "@/components/DownloadPanel";
  import ConfirmDeleteDialog from "@/components/ConfirmDeleteDialog"
  import {
    mapGetters
  } from "vuex";
  import {
    DEFAULT_BATCHSIZE,
    TEST_LIMIT,
    API_URL
  } from "@/common/config";
  import {
    LANGUAGES,
    DEFAULT_FROM,
    DEFAULT_TO,
    LanguageHelper,
  } from "@/common/language.helper";
  // import {
  //   SettingsHelper
  // } from "@/common/settings.helper";
  import {
    PROC_INIT,
    PROC_IN_PROGRESS,
    PROC_IN_PROGRESS_DONE,
    PROC_DONE,
    PROC_ERROR,
  } from "@/common/constants"
  import {
    INIT_USERSPACE,
    FETCH_ITEMS_PROCESSING,
    GET_DOC_INDEX,
    GET_PROCESSING,
    GET_PROCESSING_META,
    DELETE_ALIGNMENT,
    DOWNLOAD_SPLITTED,
    DOWNLOAD_PROCESSING,
  } from "@/store/actions.type";

  export default {
    data() {
      return {
        LANGUAGES,
        DEFAULT_FROM,
        DEFAULT_TO,
        DEFAULT_BATCHSIZE,
        TEST_LIMIT,
        API_URL,
        PROC_INIT,
        PROC_IN_PROGRESS,
        PROC_IN_PROGRESS_DONE,
        PROC_ERROR,
        PROC_DONE,
        files: LanguageHelper.initGeneralVars(),
        proxyFiles: LanguageHelper.initGeneralVars(),
        selected: LanguageHelper.initGeneralVars(),
        selectedProcessing: null,
        selectedProcessingId: null,
        currentlyProcessingId: null,
        selectedIds: LanguageHelper.initGeneralVars(),
        isLoading: {
          download: LanguageHelper.initGeneralBools(),
          processing: false,
          processingMeta: false
        },
        satisfactionEmojis: ['😍', '😄', '😁', '😊', '🙂', '😐', '🙁', '☹️', '😢', '😭'],
        downloadThreshold: 9,
        selectedListItem: 0,

        //dialogs
        showConfirmDeleteAlignmentDialog:false,

        hoverAlignmentIndex: -1,
        hoveredAlignmentItem: {"name": ""},
      };
    },
    methods: {
      downloadSplitted(langCode, openInBrowser) {
        this.$store.dispatch(DOWNLOAD_SPLITTED, {
          fileId: this.selectedIds[langCode],
          fileName: this.selected[langCode],
          username: this.$route.params.username,
          langCode,
          openInBrowser
        });
      },
      downloadProcessing(langCode) {
        this.$store.dispatch(DOWNLOAD_PROCESSING, {
          align_guid: this.selectedProcessingId,
          fileName: this.selectedProcessingId + ".txt",
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          langCodeDownload: langCode,
          format: "txt"
        });
      },
      downloadProcessingTmx() {
        this.$store.dispatch(DOWNLOAD_PROCESSING, {
          align_guid: this.selectedProcessingId,
          fileName: this.selectedProcessingId + ".tmx",
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          langCodeDownload: this.langCodeFrom,
          format: "tmx"
        });
      },
      selectProcessing(item, fileId) {
        this.selectedListItem = fileId;
        this.isLoading.processing = true;
        this.isLoading.processingMeta = true;
        this.selectedProcessing = item;
        this.selectedProcessingId = fileId;

        this.$store.dispatch(GET_PROCESSING_META, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          fileId
        }).then(() => {
          this.isLoading.processingMeta = false;
        });

        this.$store.dispatch(GET_DOC_INDEX, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          fileId
        }).then(() => {
          this.$store.dispatch(GET_PROCESSING, {
            username: this.$route.params.username,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            fileId,
            linesCount: 10,
            page: 1
          }).then(() => {
            this.isLoading.processing = false;
          });
        });
      },
      //helpers
      itemsNotEmpty(langCode) {
        if (!this.items | !this.items[langCode]) {
          return false;
        }
        return this.items[langCode].length != 0;
      },
      itemsProcessingNotEmpty(langCode) {
        if (!this.itemsProcessing | !this.itemsProcessing[langCode]) {
          return false;
        }
        return this.itemsProcessing[langCode].length != 0;
      },
      selectFirstProcessingDocument() {
        if (this.itemsProcessingNotEmpty(this.langCodeFrom)) {
          this.selectProcessing(this.itemsProcessing[this.langCodeFrom][0], this.itemsProcessing[this.langCodeFrom][0]
            .guid);
        }
      },
      selectCurrentlyProcessingDocument(item) {
        if (this.itemsProcessingNotEmpty(this.langCodeFrom)) {
          if (this.currentlyProcessingId) {
            this.selectProcessing(item, this.currentlyProcessingId);
          }
        }
      },
      collapseEditItems() {
        this.triggerCollapseEditItem = !this.triggerCollapseEditItem;
      },
      fetchAll() {
        this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo
        }).then(() => {
          let in_progress_items = this.itemsProcessing[this.langCodeFrom].filter(x => x.state[0] == 0 || x.state[
              0] ==
            1)
          if (in_progress_items.length > 0) {
            let item_index = this.itemsProcessing[this.langCodeFrom].indexOf(in_progress_items[0])
            this.currentlyProcessingId = this.itemsProcessing[this.langCodeFrom][item_index].guid
            this.userAlignInProgress = true;
            this.fetchItemsProcessingTimer();
            this.selectCurrentlyProcessingDocument(this.itemsProcessing[this.langCodeFrom][item_index]);
          } else {
            this.selectFirstProcessingDocument();
          }
        });
      },

      //deletion
      performDeleteAlignment() {
        this.$store
          .dispatch(DELETE_ALIGNMENT, {
            username: this.$route.params.username,
            guid: this.hoveredAlignmentItem.guid,
          })
          .then(() => {
            this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
              username: this.$route.params.username,
              langCodeFrom: this.langCodeFrom,
              langCodeTo: this.langCodeTo
            }).then(() => {
              this.selectFirstProcessingDocument();
            });
          });
      },
    },
    mounted() {
      this.$store.dispatch(INIT_USERSPACE, {
        username: this.$route.params.username
      }).then(() => {
        this.fetchAll();
      });
    },
    watch: {
      showProxyTo(value) {
        localStorage.showProxyTo = value
      },
      showAllTo(value) {
        localStorage.showAllTo = value ? true : false;
      },
      showAllFrom(value) {
        localStorage.showAllFrom = value ? true : false;
      },
      langCodeFrom() {
        this.fetchAll();
      },
      langCodeTo() {
        this.fetchAll();
      },
    },
    computed: {
      ...mapGetters(["items", "itemsProcessing", "splitted", "processing", "docIndex", "conflictSplittedFrom",
        "conflictSplittedTo", "conflictFlowTo", "processingMeta"
      ]),
      username() {
        return this.$route.params.username;
      },
      showAlert() {
        if (!this.items | !this.items[this.langCodeFrom] | !this.items[this.langCodeTo]) {
          return true;
        }
        return (this.items[this.langCodeFrom].length == 0) & (this.items[this.langCodeTo].length == 0);
      },
      langCodeFrom() {
        let langCode = this.$route.params.from;
        if (this.LANGUAGES[langCode]) {
          return langCode;
        }
        return DEFAULT_FROM;
      },
      langCodeTo() {
        let langCode = this.$route.params.to;
        if (this.LANGUAGES[langCode]) {
          return langCode;
        }
        return DEFAULT_TO;
      },
      thresholdText() {
        if (this.downloadThreshold == 0) {
          return "no threshold";
        } else if (this.downloadThreshold == 100) {
          return "realy?";
        }
        return (this.downloadThreshold / 100).toFixed(2);
      },
      processingExists() {
        let selected_progress_item = this.itemsProcessing[this.langCodeFrom].filter(x => x.guid_from == this
          .selectedIds[this.langCodeFrom] && x.guid_to == this.selectedIds[this.langCodeTo]);
        if (selected_progress_item.length > 0) {
          return true;
        }
        return false;
      },
      corporaSizeRelative() {
        return 5;
        // return this.selectedProcessing['sim_grades'][this.downloadThreshold] / this.selectedProcessing['sim_grades'][
        //   0
        // ] * 100;
      },
      corporaSizeAbsolute() {
        return 10;
        // return this.selectedProcessing['sim_grades'][this.downloadThreshold];
      }
    },
    components: {
      DownloadPanel,
      ConfirmDeleteDialog
    }
  };
</script>
