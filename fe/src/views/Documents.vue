<template>
  <div>

    <div class="text-h4 mt-10 font-weight-bold">
      <v-icon color="blue" large>mdi-text-box-multiple</v-icon> Documents
    </div>
    <v-alert type="info" class="mt-6" v-show="showAlert">
      There are no uploaded documents yet. Please upload some using the form
      below.
    </v-alert>
    <div class="mt-6">
      <v-row>
        <v-col cols="12" sm="6">
          <RawPanel @uploadFile="uploadFile" @onFileChange="onFileChange" @selectAndLoadPreview="selectAndLoadPreview" @performDelete="performDeleteRawFile"
            :info="LANGUAGES[langCodeFrom]" :items=items :isLoading=isLoading>
          </RawPanel>
        </v-col>
        <v-col cols="12" sm="6">
          <RawPanel @uploadFile="uploadFile" @onFileChange="onFileChange" @selectAndLoadPreview="selectAndLoadPreview" @performDelete="performDeleteRawFile"
            :info="LANGUAGES[langCodeTo]" :items=items :isLoading=isLoading>
          </RawPanel>
        </v-col>
      </v-row>
    </div>

    <div class="text-h4 mt-10 font-weight-bold">
      <v-icon color="blue" large>mdi-file-find</v-icon> Preview
    </div>
    <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2">
      Documents are splitted by sentences using language specific rules.
    </v-alert>
    <v-row>
      <v-col cols="12" sm="6">
        <SplittedPanel @onPreviewPageChange="onPreviewPageChange" @onProxyFileChange="onProxyFileChange"
          @downloadSplitted="downloadSplitted" @uploadProxyFile="uploadProxyFile" :info="LANGUAGES[langCodeFrom]"
          :splitted=splitted :selected=selected :isLoading=isLoading :showUploadProxyBtn=true>
        </SplittedPanel>
      </v-col>
      <v-col cols="12" sm="6">
        <SplittedPanel @onPreviewPageChange="onPreviewPageChange" @onProxyFileChange="onProxyFileChange"
          @downloadSplitted="downloadSplitted" @uploadProxyFile="uploadProxyFile" :info="LANGUAGES[langCodeTo]"
          :splitted=splitted :selected=selected :isLoading=isLoading :showUploadProxyBtn=true>
        </SplittedPanel>
      </v-col>
    </v-row>

  </div>
</template>

<script>
  import RawPanel from "@/components/RawPanel";
  import SplittedPanel from "@/components/SplittedPanel";
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
    INIT_USERSPACE,
    FETCH_ITEMS,
    UPLOAD_FILES,
    DELETE_DOCUMENT,
    GET_SPLITTED,
    DOWNLOAD_SPLITTED
  } from "@/store/actions.type";
  import {
    SET_SPLITTED
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
        files: LanguageHelper.initGeneralVars(),
        proxyFiles: LanguageHelper.initGeneralVars(),
        selected: LanguageHelper.initGeneralVars(),
        selectedIds: LanguageHelper.initGeneralVars(),
        isLoading: {
          upload: LanguageHelper.initGeneralBools(),
          uploadProxy: LanguageHelper.initGeneralBools(),
          download: LanguageHelper.initGeneralBools(),
          align: false,
          processing: false,
          processingMeta: false
        },
      };
    },
    methods: {
      getImgUrl(batch_id) {
        return `${API_URL}/static/img/${this.username}/${this.processingMeta.meta.align_guid}.best_${batch_id}.png?rnd=${Math.random()}`;
      },
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
      uploadFile(langCode) {
        this.isLoading.upload[langCode] = true;
        this.$store.dispatch(UPLOAD_FILES, {
            file: this.files[langCode],
            username: this.$route.params.username,
            langCode
          })
          .then(() => {
            this.$store.dispatch(FETCH_ITEMS, {
              username: this.$route.params.username,
              langCode: langCode
            }).then(() => {
              this.selectFirstDocument(langCode);
              this.isLoading.upload[langCode] = false;
            });
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
      //helpers
      itemsNotEmpty(langCode) {
        if (!this.items | !this.items[langCode]) {
          return false;
        }
        return this.items[langCode].length != 0;
      },
      selectFirstDocument(langCode) {
        if (this.itemsNotEmpty(langCode)) {
          this.selectAndLoadPreview(langCode, this.items[langCode][0].name, this.items[langCode][0].guid);
        } else {
          let data = {"items": {}, "meta": {}};
          data["items"][langCode] = []
          data["meta"][langCode] = {}
          this.$store.commit(SET_SPLITTED, {
            data,
            langCode
          });
          this.selected[langCode] = null;
        }
      },
      fetchAll() {
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
      },      
      downloadSplitted(langCode, openInBrowser) {
        this.$store.dispatch(DOWNLOAD_SPLITTED, {
          fileId: this.selectedIds[langCode],
          fileName: this.selected[langCode],
          username: this.$route.params.username,
          langCode,
          openInBrowser
        });
      },
      //deletion
      performDeleteRawFile(item, langCode) {
        this.$store.dispatch(DELETE_DOCUMENT, {
            username: this.$route.params.username,
            filename: item.name,
            guid: item.guid,
            langCode
          })
          .then(() => {
            this.$store.dispatch(FETCH_ITEMS, {
              username: this.$route.params.username,
              langCode: langCode
            }).then(() => {
              this.selectFirstDocument(langCode);
            });
          });
      }
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
      docIndex() {
        this.updateUnusedLines();
      }
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
      RawPanel,
      SplittedPanel,
    }
  };
</script>
