<template>
  <div>
    <div class="d-flex">
      <div class="text-h3 mt-5 align-self-start">
        <v-img src="@/assets/logo.png" width="50px" height="50px" />
      </div>
      <div class="text-h3 mt-5 ml-3">
        Hello, <span class="text-capitalize">{{ username }}!</span>
        <div class="text-subtitle-1 mt-2 pl-1">Let's make it parallel</div>
        <!-- <div class="text-subtitle-2 text-right">— Somebody</div> -->
      </div>
    </div>
    
    <div class="text-h4 mt-15 font-weight-bold">💾 Documents</div>
    <v-alert type="info" class="mt-6" v-show="showAlert">
      There are no uploaded documents yet. Please upload some using the form
      below.
    </v-alert>
    <div class="mt-6">
      <v-row>
        <v-col cols="12" sm="6">
          <RawPanel @uploadFile="uploadFile" @onFileChange="onFileChange" @selectAndLoadPreview="selectAndLoadPreview"
            :info="LANGUAGES[langCodeFrom]" :items=items :isLoading=isLoading>
          </RawPanel>
        </v-col>
        <v-col cols="12" sm="6">
          <RawPanel @uploadFile="uploadFile" @onFileChange="onFileChange" @selectAndLoadPreview="selectAndLoadPreview"
            :info="LANGUAGES[langCodeTo]" :items=items :isLoading=isLoading>
          </RawPanel>
        </v-col>
      </v-row>
    </div>

    <div class="text-h4 mt-10 font-weight-bold">🔍 Preview</div>
    <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2">
      Documents are splitted by sentences using language specific rules.
    </v-alert>
    <v-row>
      <v-col cols="12" sm="6">
        <SplittedPanel
          @onPreviewPageChange="onPreviewPageChange"
          @onProxyFileChange="onProxyFileChange"
          @downloadSplitted="downloadSplitted"
          @uploadProxyFile="uploadProxyFile"
          :info="LANGUAGES[langCodeFrom]"
          :splitted=splitted
          :selected=selected
          :isLoading=isLoading
          :showUploadProxyBtn=false>
        </SplittedPanel>
      </v-col>
      <v-col cols="12" sm="6">
        <SplittedPanel
          @onPreviewPageChange="onPreviewPageChange"
          @onProxyFileChange="onProxyFileChange"
          @downloadSplitted="downloadSplitted"
          @uploadProxyFile="uploadProxyFile"
          :info="LANGUAGES[langCodeTo]"
          :splitted=splitted
          :selected=selected
          :isLoading=isLoading
          :showUploadProxyBtn=true>
        </SplittedPanel>
      </v-col>
    </v-row>

    <div class="text-h4 mt-10 font-weight-bold">⚖️ Alignment</div>
    <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2">
      This is a test version. Only {{TEST_LIMIT}} lines will be aligned.
    </v-alert>
    <v-row class="mt-6">
      <v-col cols="12" sm="6">
        <InfoPanel :info="LANGUAGES[langCodeFrom]" :splitted=splitted :selected=selected></InfoPanel>
      </v-col>
      <v-col cols="12" sm="6">
        <InfoPanel :info="LANGUAGES[langCodeTo]" :splitted=splitted :selected=selected></InfoPanel>
      </v-col>
    </v-row>
    <v-btn v-if="!userAlignInProgress" v-show="selected[langCodeFrom] && selected[langCodeTo]" class="success mt-6"
      :loading="isLoading.align || isLoading.alignStopping" :disabled="isLoading.align || isLoading.alignStopping"
      @click="align()">
      Align documents
    </v-btn>
    <v-btn v-else v-show="selected[langCodeFrom] && selected[langCodeTo]" class="error mt-6" @click="stopAlignment()">
      Stop alignment
    </v-btn>

    <div class="text-h4 mt-10 font-weight-bold">✒️ Result</div>

    <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2"
      v-if="!itemsProcessing || !itemsProcessing[langCodeFrom] || (itemsProcessing[langCodeFrom].length == 0)">
      There are no previously aligned documents yet.
    </v-alert>

    <!-- PROCESSING DOCUMENTS LIST BLOCK -->
    <div v-else class="mt-6">
      <v-card>
        <div class="green lighten-5" dark>
          <v-card-title>Documents</v-card-title>
          <v-card-text>List of previosly aligned documents</v-card-text>
        </div>
        <v-divider></v-divider>
        <v-list class="pa-0">
          <v-list-item-group mandatory color="gray">
            <v-list-item v-for="(item, i) in itemsProcessing[langCodeFrom]" :key="i"
              @change="selectProcessing(item, i)">
              <v-list-item-icon>
                <v-icon v-if="item.state[0]==PROC_INIT || item.state[0]==PROC_IN_PROGRESS" color="blue">
                  mdi-clock-outline</v-icon>
                <v-icon v-else-if="item.state[0]==PROC_ERROR" color="error">mdi-alert-circle</v-icon>
                <v-icon v-else color="teal">mdi-check</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title v-text="item.name"></v-list-item-title>
              </v-list-item-content>
              <v-progress-linear stream buffer-value="0" :value="item.state[2]/item.state[1] * 100" color="green"
                :active="item.state[0]==PROC_INIT || item.state[0]==PROC_IN_PROGRESS" absolute bottom>
              </v-progress-linear>
            </v-list-item>
          </v-list-item-group>
        </v-list>
      </v-card>

      <div class="text-h5 mt-10 font-weight-bold">Visualization</div>

      <v-alert v-if="!selectedProcessing || !selectedProcessing.imgs || selectedProcessing.imgs.length == 0" type="info"
        border="left" colored-border color="purple" class="mt-6" elevation="2">
        Images will start showing after the first batch completion.
      </v-alert>
      <v-row v-else class="mt-6">
        <v-col v-for="(img, i) in selectedProcessing.imgs" :key=i cols="12" sm="3">
          <v-card>
            <div class="grey lighten-5">
              <v-card-title>
                batch {{i+1}}
                <v-spacer></v-spacer>
                <v-chip color="grey" text-color="black" small outlined>
                  {{DEFAULT_BATCHSIZE * i + 1}} — {{DEFAULT_BATCHSIZE * (i + 1)}}
                </v-chip>
              </v-card-title>
            </div>
            <v-divider></v-divider>
            <v-img :src="`${API_URL}/static/img/${username}/${img}`" :lazy-src="`${API_URL}/static/proc_img_stub.jpg`">
              <template v-slot:placeholder>
                <v-row class="fill-height ma-0" align="center" justify="center">
                  <v-progress-circular indeterminate color="green"></v-progress-circular>
                </v-row>
              </template>
            </v-img>
          </v-card>
        </v-col>
      </v-row>

      <div class="text-h5 mt-10 font-weight-bold">Edit</div>

      <div class="text-center" v-if="isLoading.processing">
        <v-progress-circular indeterminate color="green"></v-progress-circular>
      </div>
      <v-alert v-else-if="selectedProcessing && selectedProcessing.state[0]==PROC_ERROR" type="error" border="left"
        colored-border color="error" class="mt-6" elevation="2">
        Error occured. Please, write to @averkij.
      </v-alert>
      <v-alert v-else-if="!processing || !processing.items || processing.items.length == 0" type="info" border="left"
        colored-border color="info" class="mt-6" elevation="2">
        Please, wait. Alignment is in progress.
      </v-alert>

      <!-- EDIT ITEMS block-->
      <v-card v-else class="mt-6">
        <div class="green lighten-5" dark>

          <!-- title -->
          <v-card-title class="pr-3">
            {{selectedProcessing.name}}
            <v-spacer></v-spacer>

            <v-icon>mdi-translate</v-icon>  
            <v-switch value="true" v-model="showProxyTo" class="mx-2"></v-switch>
            <!-- <div>showTranslation: {{clientSettings}}</div> -->

            <v-btn icon @click="collapseEditItems">
              <v-icon>mdi-collapse-all</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>Review and edit automatically aligned document</v-card-text>
        </div>
        <v-divider></v-divider>

        <!-- items -->
        <div v-for="(line, i) in processing.items" :key="i">
          <EditItem @editProcessing="editProcessing"
                    @editAddUpEnd="editAddUpEnd"
                    @editAddDownEnd="editAddDownEnd"
                    @editDeleteLine="editDeleteLine"
                    @editAddEmptyLineBefore="editAddEmptyLineBefore"
                    @editAddEmptyLineAfter="editAddEmptyLineAfter"
                    @editClearLine="editClearLine"
                    @getCandidates="getCandidates"
                    @editAddCandidateEnd="editAddCandidateEnd"
                    :item="line"
                    :prevItem="i == 0 ? processing.items[0] : processing.items[i-1]"
                    :collapse="triggerCollapseEditItem"
                    :clearCandidates="triggerClearCandidates"
                    :showProxyTo="showProxyTo">
          </EditItem>
          <v-divider></v-divider>
        </div>

        <!-- pagination -->
        <div class="text-center pa-3">
          <v-pagination v-model="processing.meta.page" :length="processing.meta.total_pages" total-visible="10"
            @input="onProcessingPageChange(processing.meta.page)">
          </v-pagination>
        </div>
      </v-card>     

      <!-- <div class="text-h4 mt-10 font-weight-bold">🧩 Unused strings</div>

      <v-alert v-if="!processing || !processing.items || processing.items.length == 0" type="info" border="left"
        colored-border color="info" class="mt-6" elevation="2">
        Please, wait. Alignment is in progress.
      </v-alert>
      <div v-else>
        <div></div>
        {{docIndex}}
      </div> -->

      <div class="text-h4 mt-10 font-weight-bold">🍍 Corpora</div>

      <v-alert v-if="!processing || !processing.items || processing.items.length == 0" type="info" border="left"
        colored-border color="info" class="mt-6" elevation="2">
        Please, wait. Alignment is in progress.
      </v-alert>
      <div v-else>
        <div class="mt-10">
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
              <!-- <div class="text-h5 black--text">sentences</div> -->
            </v-progress-circular>
          </div>
        </div>
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
        <v-btn class="primary ma-5" @click="downloadProcessingTmx()">Download</v-btn>
      </div>
    </div>
  </div>
</template>

<script>
  import RawPanel from "@/components/RawPanel";
  import DownloadPanel from "@/components/DownloadPanel";
  import SplittedPanel from "@/components/SplittedPanel";
  import InfoPanel from "@/components/InfoPanel";
  import EditItem from "@/components/EditItem";
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
  import {
    SettingsHelper
  } from "@/common/settings.helper";
  import {
    RESULT_OK,
    RESULT_ERROR,
    PROC_INIT,
    PROC_IN_PROGRESS,
    PROC_DONE,
    PROC_ERROR,
    EDIT_ADD_PREV_END,
    EDIT_ADD_NEXT_END,
    EDIT_ADD_CANDIDATE_END,
    EDIT_DELETE_LINE,
    EDIT_CLEAR_LINE,
    EDIT_LINE,
    ADD_EMPTY_LINE_BEFORE,
    ADD_EMPTY_LINE_AFTER
  } from "@/common/constants"
  import {
    FETCH_ITEMS,
    FETCH_ITEMS_PROCESSING,
    UPLOAD_FILES,
    GET_SPLITTED,
    GET_DOC_INDEX,
    GET_PROCESSING,
    GET_CANDIDATES,
    STOP_ALIGNMENT,
    EDIT_PROCESSING,
    ALIGN_SPLITTED,
    DOWNLOAD_SPLITTED,
    DOWNLOAD_PROCESSING
  } from "@/store/actions.type";
  import {
    SET_ITEMS_PROCESSING,
  } from "@/store/mutations.type";

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
        proxyFiles: LanguageHelper.initGeneralVars(),
        selected: LanguageHelper.initGeneralVars(),
        selectedProcessing: null,
        selectedProcessingId: null,
        currentlyProcessing: null,
        currentlyProcessingId: null,
        selectedIds: LanguageHelper.initGeneralVars(),
        isLoading: {
          upload: LanguageHelper.initGeneralBools(),
          uploadProxy: LanguageHelper.initGeneralBools(),
          download: LanguageHelper.initGeneralBools(),
          align: false,
          processing: false
        },
        triggerCollapseEditItem: false,
        triggerClearCandidates:false ,
        userAlignInProgress: false,
        satisfactionEmojis: ['😍', '😄', '😁', '😊', '🙂', '😐', '🙁', '☹️', '😢', '😭'],
        downloadThreshold: 9,
        showProxyTo: SettingsHelper.getShowProxyTo()
      };
    },
    methods: {
      onFileChange(file, langCode) {
        this.files[langCode] = file;
      },
      onProxyFileChange(file, langCode) {
        this.proxyFiles[langCode] = file;
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
        this.triggerClearCandidates = !this.triggerClearCandidates;
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
      uploadProxyFile(langCode) {
        this.isLoading.uploadProxy[langCode] = true;
        this.$store
          .dispatch(UPLOAD_FILES, {
            file: this.proxyFiles[langCode],
            username: this.$route.params.username,
            langCode,
            isProxy: true,
            rawFileName: this.selected[langCode]
          })
          .then(() => {
            this.isLoading.uploadProxy[langCode] = false;
          });
      },
      getCandidates(indexId, textType, countBefore, countAfter, callback) {
        this.$store.dispatch(GET_CANDIDATES, {
            username: this.$route.params.username,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            fileId: this.selectedProcessingId,
            textType: textType,
            countBefore: countBefore,
            countAfter: countAfter
        }).then(function (response) {
          callback(RESULT_OK, response.data)
        }).catch(() => {
          callback(RESULT_ERROR)
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
      },
      selectProcessing(item, fileId) {
        this.isLoading.processing = true;
        this.selectedProcessing = item;
        this.selectedProcessingId = fileId;

        console.log("aaaa")

        this.$store.dispatch(GET_DOC_INDEX, {
          username: this.$route.params.username,
          langCodeFrom: this.langCodeFrom,
          langCodeTo: this.langCodeTo,
          fileId
        }).then(() => {
          console.log("document index", this.docIndex)

          this.$store.dispatch(GET_PROCESSING, {
            username: this.$route.params.username,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            fileId,
            linesCount: 10,
            page: 1
          }).then(() => {
            console.log("processing", this.processing)
            this.isLoading.processing = false;
          });
        });
      },
      refreshProcessingPage() {
        this.$store.dispatch(GET_PROCESSING, {
            username: this.$route.params.username,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            fileId: this.selectedProcessingId,
            linesCount: 10,
            page: this.processing.meta.page
          });
      },
      editAddCandidateEnd(indexId, textType, candidateLineId, candidateText) {
        this.$store.dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            candidateLineId: candidateLineId,
            candidateText: candidateText,
            text_type: textType,
            operation: EDIT_ADD_CANDIDATE_END,
            target: "previous"
          }).then(() => {
            this.refreshProcessingPage();
          });
      },
      editAddUpEnd(indexId, editItemToText, textType) {
        this.$store.dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            text: editItemToText,
            text_type: textType,
            operation: EDIT_ADD_PREV_END,
            target: "previous"
          }).then(() => {
            this.refreshProcessingPage();
          });
      },
      editAddDownEnd(indexId, editItemText, textType) {
        console.log("textType", textType)
        this.$store.dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            text: editItemText,
            text_type: textType,
            operation: EDIT_ADD_NEXT_END,
            target: "next"
          }).then(() => {
            this.refreshProcessingPage();
          });
      },
      editAddEmptyLineBefore(indexId) {
        this.$store.dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            operation: ADD_EMPTY_LINE_BEFORE
          }).then(() => {
            this.refreshProcessingPage()          
          });
      },
      editAddEmptyLineAfter(indexId) {
        this.$store.dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            operation: ADD_EMPTY_LINE_AFTER
          }).then(() => {
            this.refreshProcessingPage()          
          });
      },
      editDeleteLine(indexId) {
        this.$store.dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            operation: EDIT_DELETE_LINE
          }).then(() => {
            this.refreshProcessingPage()          
          });
      },
      editClearLine(indexId, textType) {
        this.$store.dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            text_type: textType,
            operation: EDIT_CLEAR_LINE
          }).then(() => {
            this.refreshProcessingPage()          
          });
      },
      editProcessing(indexId, editItemText, textType, callback) {
        this.$store
          .dispatch(EDIT_PROCESSING, {
            username: this.$route.params.username,
            fileId: this.selectedProcessingId,
            langCodeFrom: this.langCodeFrom,
            langCodeTo: this.langCodeTo,
            indexId: indexId,
            text: editItemText,
            text_type: textType,
            operation: EDIT_LINE
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
              langCodeTo: this.langCodeTo
            }).then(() => {
              this.selectCurrentlyProcessingDocument();
            });

            this.fetchItemsProvessingTimer();
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
        this.$store
          .commit(SET_ITEMS_PROCESSING, {
            items: processingItems,
            langCode: this.langCodeFrom
          });
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
          this.selectAndLoadPreview(langCode, this.items[langCode][0].name, 0);
        }
      },
      selectFirstProcessingDocument() {
        console.log("this.itemsProcessing", this.itemsProcessing)
        if (this.itemsProcessingNotEmpty(this.langCodeFrom)) {
          this.selectProcessing(this.itemsProcessing[this.langCodeFrom][0], 0);
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
            langCodeTo: this.langCodeTo
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
      });
      this.$store.dispatch(FETCH_ITEMS, {
        username: this.$route.params.username,
        langCode: this.langCodeTo
      }).then(() => {
        this.selectFirstDocument(this.langCodeTo);
      });
      this.$store.dispatch(FETCH_ITEMS_PROCESSING, {
        username: this.$route.params.username,
        langCodeFrom: this.langCodeFrom,
        langCodeTo: this.langCodeTo
      }).then(() => {
        if (this.itemsProcessing[this.langCodeFrom].filter(x => x.state[0] == 0 || x.state[0] == 1).length > 0) {
          this.userAlignInProgress = true;
          this.fetchItemsProvessingTimer();
        }
        this.selectFirstProcessingDocument();
      });
      if (localStorage.showProxyTo) {
        this.showProxyTo = localStorage.showProxyTo;
      }
    },
    watch: {
      showProxyTo(value) {
        localStorage.showProxyTo = value
      }
    },
    computed: {
      ...mapGetters(["items", "itemsProcessing", "splitted", "processing", "docIndex"]),
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
      EditItem,
      RawPanel,
      DownloadPanel,
      SplittedPanel,
      InfoPanel
    }
  };
</script>