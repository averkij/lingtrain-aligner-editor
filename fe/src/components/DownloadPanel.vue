<template>
  <v-card>
    <div class="blue lighten-5">
      <v-card-title>{{ info.icon }} {{ info.name }}</v-card-title>
      <!-- <v-card-text>Your {{ info.name }} files</v-card-text> -->
    </div>
    <v-divider></v-divider>
    <v-card-title>Download</v-card-title>
    <v-card-text>Aligned {{ info.name }} corpora in txt format.</v-card-text>
    <v-divider class="mt-10"></v-divider>
    <v-card-actions>
      <v-btn @click="downloadFile(info.langCode)" :loading="isLoading.download[info.langCode]"
        :disabled="isLoading.download[info.langCode]">
        <v-icon left color="grey">mdi-download</v-icon>Download
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
  export default {
    name: "DownloadPanel",
    props: ["info", "isLoading", "countOrig", "count"],
    methods: {
      downloadFile(langCode) {
        this.$emit('downloadFile', langCode)
      }
    },
    computed: {}
  };
</script>
