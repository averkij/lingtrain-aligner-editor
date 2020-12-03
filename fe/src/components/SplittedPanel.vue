<template> 
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
      <v-spacer />
      <v-btn @click="updloadSplittedTranslation(info.langCode)">Upload translation</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
  import PreviewItem from "@/components/PreviewItem";
  export default {
    name: "SplittedPanel",
    props: ["info", "splitted", "selected"],
    methods: {
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