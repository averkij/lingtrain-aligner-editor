<template>
  <div>
    <v-alert type="info" border="left" colored-border color="blue" class="mt-6" elevation="2" v-if="
              !splitted |
                !splitted[info.langCode] |
                (splitted[info.langCode].lines.length == 0)
            ">
      Select file to preview.
    </v-alert>
    <v-card v-else>
      <div class="yellow lighten-5">
        <v-card-title>{{ selected[info.langCode] }}</v-card-title>
        <v-card-text>{{
                  splitted[info.langCode].meta.lines_count | separator
                }}
          lines</v-card-text>
      </div>
      <v-divider></v-divider>
      <div v-for="(line, i) in splitted[info.langCode].lines" :key="i">
        <PreviewItem :item="line"></PreviewItem>
        <v-divider></v-divider>
      </div>
      <div class="text-center pa-3">
        <v-pagination v-model="splitted[info.langCode].meta.page" :length="splitted[info.langCode].meta.total_pages"
          total-visible="7" @input="
                  onPreviewPageChange(
                    splitted[info.langCode].meta.page,
                    info.langCode
                  )
                ">
        </v-pagination>
      </div>
      <v-divider></v-divider>
      <v-card-actions>
        <v-btn @click="downloadSplitted(info.langCode)">Download</v-btn>
        <v-spacer></v-spacer>
        <v-btn v-if="showUploadProxyBtn" @click="showUploadProxyPanel = true">Add translation</v-btn>
      </v-card-actions>
    </v-card>

    <v-card v-if="showUploadProxyPanel" class="mt-5">
      <v-card-title>Upload translation</v-card-title>
      <v-card-text>Optionally add translation for the downloaded file.</v-card-text>
      <v-card-actions>
        <v-file-input outlined dense accept=".txt" @change="onProxyFileChange($event, info.langCode)">
        </v-file-input>
      </v-card-actions>
      <v-divider></v-divider>
      <v-card-actions>
        <v-btn @click="uploadProxyFile(info.langCode)" :loading="isLoading.uploadProxy[info.langCode]"
          :disabled="isLoading.uploadProxy[info.langCode]">
          Upload
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
  import PreviewItem from "@/components/PreviewItem";
  export default {
    name: "SplittedPanel",
    props: ["info", "splitted", "selected", "isLoading", "showUploadProxyBtn"],
    data () {
      return {
        showUploadProxyPanel: false
      }
    },
    methods: {
      onProxyFileChange(event, langCode) {
        this.$emit('onProxyFileChange', event, langCode)
      },
      uploadProxyFile(langCode) {
        this.$emit('uploadProxyFile', langCode)
      },
      onPreviewPageChange(page, langCode) {
        this.$emit('onPreviewPageChange', page, langCode)
      },
      downloadSplitted(langCode) {
        this.$emit('downloadSplitted', langCode)
      }
    },
    components: {
      PreviewItem
    }
  };
</script>
