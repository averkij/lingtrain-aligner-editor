<template>
  <div>
    <div class="d-flex">
      <div class="text-h3 mt-5 ml-3">
        <span class="text-capitalize">Lexigraph</span>
        <!-- ✒️ Hello, <span class="text-capitalize">{{ username }}!</span> -->
        <div class="text-subtitle-1 mt-2 pl-1">Строим графы из текста</div>
        <!-- <div class="text-subtitle-2 text-right">— Somebody</div> -->
      </div>
    </div>

    <!-- RAW panels -->
    <div class="text-h4 mt-15 font-weight-bold">💾 Документы</div>
    <v-alert type="info" class="mt-6" v-show="showAlert">
      There are no uploaded documents yet. Please upload some using the form
      below.
    </v-alert>
    <div class="mt-6">
      <v-row>
        <v-col cols="12" sm="12">
          <RawPanel @uploadFile="uploadFile" @onFileChange="onFileChange" @selectAndLoadPreview="selectAndLoadPreview"
            :info="LANGUAGES[langCodeFrom]" :items=items :isLoading=isLoading>
          </RawPanel>
        </v-col>
      </v-row>
    </div>

    <!-- SPLITTED panels -->
    <div v-show="false">
    <div class="text-h4 mt-10 font-weight-bold">🔍 Preview</div>
    <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2">
      Documents are splitted by sentences using language specific rules.
    </v-alert>
    <v-row>
      <v-col cols="12" sm="6">
        <SplittedPanel @onPreviewPageChange="onPreviewPageChange" @downloadSplitted="downloadSplitted"
          :info="LANGUAGES[langCodeFrom]" :splitted=splitted :selected=selected>
        </SplittedPanel>
      </v-col>
      <v-col cols="12" sm="6">
        <SplittedPanel @onPreviewPageChange="onPreviewPageChange" @downloadSplitted="downloadSplitted"
          :info="LANGUAGES[langCodeTo]" :splitted=splitted :selected=selected>
        </SplittedPanel>
      </v-col>
    </v-row>
    </div>

    <!-- ALIGN panels -->
    <div class="text-h4 mt-10 font-weight-bold">💡 Расчеты</div>
    <v-alert v-show="false" type="info" border="left" colored-border color="blue" class="mt-6" elevation="2">
      This is a test version. Only {{TEST_LIMIT}} lines will be aligned.
    </v-alert>
    <v-row class="mt-6">
      <v-col cols="12" sm="12">
        <InfoPanel :info="LANGUAGES[langCodeFrom]" :splitted=splitted :selected=selected></InfoPanel>
      </v-col>
      <!-- <v-col cols="12" sm="6" >
        <InfoPanel :info="LANGUAGES[langCodeTo]" :splitted=splitted :selected=selected></InfoPanel>
      </v-col> -->
    </v-row>
    <!-- <v-btn v-if="!userAlignInProgress" v-show="selected[langCodeFrom] && selected[langCodeTo]" class="success mt-6"
      :loading="isLoading.align || isLoading.alignStopping" :disabled="isLoading.align || isLoading.alignStopping"
      @click="align()">
      Align documents
    </v-btn>
    <v-btn v-else v-show="selected[langCodeFrom] && selected[langCodeTo]" class="error mt-6" @click="stopAlignment()">
      Stop alignment
    </v-btn>  -->
    <v-btn v-if="!userAlignInProgress" v-show="selected[langCodeFrom]" class="success mt-6"
      :loading="isLoading.align || isLoading.alignStopping" :disabled="isLoading.align || isLoading.alignStopping"
      @click="calculateGraphs()">
      Посчитать
    </v-btn>
    <v-btn v-else v-show="selected[langCodeFrom]" class="error mt-6" @click="stopAlignment()">
      Stop alignment
    </v-btn> 

    <!-- PROCESSING panels -->
    <div class="text-h4 mt-10 font-weight-bold">✒️ Результат</div>

    <div class="text-h5 mt-10 font-weight-bold">Наибольшие связи между буквами</div>
    <div class="mt-6">
      <!-- {{itemsProcessing}} -->
      <p v-html="itemsProcessing['ru'].conn_html"></p>
    </div>

    <div class="text-h5 mt-10 font-weight-bold">Степени букв</div>
    <div class="mt-6">
      <p v-html="itemsProcessing['ru'].deg_html"></p>
    </div>

    <div class="text-h5 mt-10 font-weight-bold">Центральности букв</div>
    <div class="mt-6">
      <p v-html="itemsProcessing['ru'].centr_html"></p>
    </div>

    <div class="text-h5 mt-10 font-weight-bold">Плотность связей букв</div>
    <div class="mt-6">
      {{itemsProcessing['ru'].density}}
    </div>

    <div class="text-h5 mt-10 font-weight-bold">Спектр графа (собственные векторы)</div>
    <div class="mt-6">
      <p v-html="itemsProcessing['ru'].spectr_html"></p>
    </div>

    <!-- <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2"
      v-if="!itemsProcessing || !itemsProcessing[langCodeFrom] || (itemsProcessing[langCodeFrom].length == 0)">
      There are no previously aligned documents yet.
    </v-alert> -->

  </div>
</template>

<script>
  import RawPanel from "@/components/RawPanel";
  // import DownloadPanel from "@/components/DownloadPanel";
  import SplittedPanel from "@/components/SplittedPanel";
  import InfoPanel from "@/components/InfoPanel";
  // import EditItem from "@/components/EditItem";
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
    LanguageHelper
  } from "@/common/language.helper";
  import {
    RESULT_OK,
    RESULT_ERROR,
    PROC_INIT,
    PROC_IN_PROGRESS,
    PROC_DONE,
    PROC_ERROR,
  } from "@/common/constants"
  import {
    FETCH_ITEMS,
    FETCH_ITEMS_PROCESSING,
    UPLOAD_FILES,
    GET_SPLITTED,
    GET_PROCESSING,
    STOP_ALIGNMENT,
    EDIT_PROCESSING,
    ALIGN_SPLITTED,
    DOWNLOAD_SPLITTED,
    DOWNLOAD_PROCESSING
  } from "@/store/actions.type";
  // import {
  //   SET_ITEMS_PROCESSING,
  // } from "@/store/mutations.type";

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
        PROC_ERROR,
        PROC_DONE,
        files: LanguageHelper.initGeneralVars(),
        selected: LanguageHelper.initGeneralVars(),
        selectedProcessing: null,
        selectedProcessingId: null,
        currentlyProcessing: null,
        currentlyProcessingId: null,
        selectedIds: LanguageHelper.initGeneralVars(),
        isLoading: {
          upload: LanguageHelper.initGeneralBools(),
          download: LanguageHelper.initGeneralBools(),
          align: false,
          processing: false
        },
        triggerCollapseEditItem: false,
        userAlignInProgress: false,
        satisfactionEmojis: ['😍', '😄', '😁', '😊', '🙂', '😐', '🙁', '☹️', '😢', '😭'],
        downloadThreshold: 9
      };
    },
    methods: {
      onFileChange(file, langCode) {
        this.files[langCode] = file;

      },
      onPreviewPageChange(page, langCode) {
        this.$store.dispatch(GET_SPLITTED, {
          username: this.$route.params.username,
          langCode,
          fileId: this.selectedIds[langCode],
          linesCount: 10,
          page: page
        });
      },
      onProcessingPageChange(page) {
        this.triggerCollapseEditItem = !this.triggerCollapseEditItem;
        this.$store.dispatch(GET_PROCESSING, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          fileId: this.selectedProcessingId,
          linesCount: 10,
          page: page
        });
      },
      uploadFile(langCode) {
        this.isLoading.upload[langCode] = true;
        this.$store
          .dispatch(UPLOAD_FILES, {
            file: this.files[langCode],
            username: this.$route.params.username,
            langCode
          })
          .then(() => {
            this.isLoading.upload[langCode] = false;
            this.selectFirstDocument(langCode);
          });
      },
      downloadSplitted(langCode) {
        this.$store.dispatch(DOWNLOAD_SPLITTED, {
          fileId: this.selectedIds[langCode],
          fileName: this.selected[langCode],
          username: this.$route.params.username,
          langCode
        });
      },
      downloadProcessing(langCode) {
        this.$store.dispatch(DOWNLOAD_PROCESSING, {
          fileId: this.selectedIds[this.langCodeFrom],
          fileName: this.selected[this.langCodeFrom],
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          langCodeDownload: langCode,
          format: "txt",
          threshold: this.downloadThreshold
        });
      },
      downloadProcessingTmx() {
        this.$store.dispatch(DOWNLOAD_PROCESSING, {
          fileId: this.selectedIds[this.langCodeFrom],
          fileName: this.selected[this.langCodeFrom] + ".tmx",
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          langCodeDownload: this.langCodeFrom,
          format: "tmx",
          threshold: this.downloadThreshold
        });
      },
      selectAndLoadPreview(langCode, name, fileId) {
        this.selected[langCode] = name;
        this.selectedIds[langCode] = fileId;
        this.$store.dispatch(GET_SPLITTED, {
          username: this.$route.params.username,
          langCode,
          fileId,
          linesCount: 10,
          page: 1
        });
        this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          fileId: this.selectedIds[this.langCodeFrom]
        }).then(() => {
          // this.selectCurrentlyProcessingDocument();
        });
      },
      selectProcessing(item, fileId) {
        this.isLoading.processing = true;
        this.selectedProcessing = item;
        this.selectedProcessingId = fileId;
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
      },
      editProcessing(line_id, text, text_type, callback) {
        this.$store
          .dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            line_id: line_id,
            text: text,
            text_type: text_type
          }).then(function () {
            callback(RESULT_OK)
          }).catch(() => {
            callback(RESULT_ERROR)
          });
      },
      align() {
        this.isLoading.align = true;
        this.initProcessingDocument();
        this.currentlyProcessing = this.selected[this.langCodeFrom]
        this.$store
          .dispatch(ALIGN_SPLITTED, {
            username: this.$route.params.username,
            fileIds: this.selectedIds,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo
          })
          .then(() => {
            this.userAlignInProgress = true;
            this.isLoading.align = false;

            this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
              username: this.$route.params.username,
              langCodeFrom: this.langCodeFrom,
              langCodeTo: this.langCodeTo,
              fileId: this.selectedIds[this.langCodeFrom]
            }).then(() => {
              this.selectCurrentlyProcessingDocument();
            });

            this.fetchItemsProvessingTimer();
          });
      },
      calculateGraphs() {
        // alert(this.selected[this.langCodeFrom])

        this.isLoading.align = true;
        this.currentlyProcessing = this.selected[this.langCodeFrom]
        
        this.$store
          .dispatch(ALIGN_SPLITTED, {
            username: this.$route.params.username,
            fileIds: this.selectedIds,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo
          })
          .then(() => {
            this.userAlignInProgress = true;
            this.isLoading.align = false;

            this.userAlignInProgress = false;
            this.isLoading.alignStopping = false;


            this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
              username: this.$route.params.username,
              langCodeFrom: this.langCodeFrom,
              langCodeTo: this.langCodeTo,
              fileId: this.selectedIds[this.langCodeFrom]
            }).then(() => {
              // this.selectCurrentlyProcessingDocument();
            });

            // this.fetchItemsProvessingTimer();
          });
      },
      stopAlignment() {
        this.userAlignInProgress = false;
        this.isLoading.alignStopping = true;
        this.$store.dispatch(STOP_ALIGNMENT, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          fileId: this.currentlyProcessingId
        });
      },
      initProcessingDocument() {
        let processingItems = JSON.parse(JSON.stringify(this.itemsProcessing[this.langCodeFrom]));
        let currentIndex = -1;
        if (this.itemsProcessingNotEmpty(this.langCodeFrom)) {
          currentIndex = processingItems.findIndex(x => x.name == this.selected[this.langCodeFrom]);
        }
        if (currentIndex >= 0) {
          processingItems.splice(currentIndex, 1, {
            "imgs": [],
            "name": this.selected[this.langCodeFrom],
            "state": [0, 3, 0]
          });
        } else {
          processingItems.push({
            "imgs": [],
            "name": this.selected[this.langCodeFrom],
            "state": [0, 3, 0]
          });
        }
        // this.$store
        //   .commit(SET_ITEMS_PROCESSING, {
        //     items: processingItems,
        //     langCode: this.langCodeFrom
        //   });
      },
      //helpers
      itemsNotEmpty(langCode) {
        if (!this.items | !this.items[langCode]) {
          return true;
        }
        return this.items[langCode].length != 0;
      },
      itemsProcessingNotEmpty(langCode) {
        if (!this.itemsProcessing | !this.itemsProcessing[langCode]) {
          return false;
        }
        return this.itemsProcessing[langCode].length != 0;
      },
      selectFirstDocument(langCode) {
        if (this.itemsNotEmpty(langCode) & !this.selected[langCode]) {
          this.selectAndLoadPreview(langCode, this.items[langCode][0], 0);
        }
      },
      selectFirstProcessingDocument() {
        if (this.itemsProcessingNotEmpty(this.langCodeFrom)) {
          // this.selectProcessing(this.itemsProcessing[this.langCodeFrom][0], 0);
        }
      },
      selectCurrentlyProcessingDocument() {
        if (this.itemsProcessingNotEmpty(this.langCodeFrom)) {
          this.currentlyProcessingId = this.itemsProcessing[this.langCodeFrom].findIndex(x => x.name == this
            .currentlyProcessing);
          console.log(this.currentlyProcessing, this.currentlyProcessingId)
          if (this.currentlyProcessingId >= 0) {
            this.selectProcessing(this.itemsProcessing[this.langCodeFrom][this.currentlyProcessingId], this
              .currentlyProcessingId);
          }
        }
      },
      collapseEditItems() {
        this.triggerCollapseEditItem = !this.triggerCollapseEditItem;
      },
      fetchItemsProvessingTimer() {
        setTimeout(() => {
          this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
            username: this.$route.params.username,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            fileId: this.selectedIds[this.langCodeFrom]
          }).then(() => {
            if (this.itemsProcessing[this.langCodeFrom].filter(x => x.state[0] == 0 || x.state[0] == 1).length >
              0) {
              this.userAlignInProgress = true;
              this.fetchItemsProvessingTimer();
            } else {
              this.userAlignInProgress = false;
              this.isLoading.alignStopping = false;
              this.selectCurrentlyProcessingDocument();
            }
            this.selectProcessing(this.itemsProcessing[this.langCodeFrom][0], 0)
          });
        }, 5000)
      }
    },
    mounted() {
      this.$store.dispatch(FETCH_ITEMS, {
        username: this.$route.params.username,
        langCode: this.langCodeFrom
      }).then(() => {
        this.selectFirstDocument(this.langCodeFrom);
        this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          fileId: this.selectedIds[this.langCodeFrom]
        });
      });
      // this.$store.dispatch(FETCH_ITEMS, {
      //   username: this.$route.params.username,
      //   langCode: this.langCodeTo
      // }).then(() => {
      //   this.selectFirstDocument(this.langCodeTo);
      // });
      // this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
      //   username: this.$route.params.username,
      //   langCodeFrom: this.langCodeFrom,
      //   langCodeTo: this.langCodeTo,
      //   fileId: this.selectedIds[this.langCodeFrom]
      // }).then(() => {
      //   if (this.itemsProcessing[this.langCodeFrom].filter(x => x.state[0] == 0 || x.state[0] == 1).length > 0) {
      //     this.userAlignInProgress = true;
      //     this.fetchItemsProvessingTimer();
      //   }
      //   this.selectFirstProcessingDocument();
      // });
    },
    computed: {
      ...mapGetters(["items", "itemsProcessing", "splitted", "processing"]),
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
      corporaSizeRelative() {
        return this.selectedProcessing['sim_grades'][this.downloadThreshold] / this.selectedProcessing['sim_grades'][
          0
        ] * 100;
      },
      corporaSizeAbsolute() {
        return this.selectedProcessing['sim_grades'][this.downloadThreshold];
      }
    },
    components: {
      // EditItem,
      RawPanel,
      // DownloadPanel,
      SplittedPanel,
      InfoPanel
    }
  };
</script>