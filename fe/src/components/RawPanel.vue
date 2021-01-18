<template>
  <v-card>
    <!-- <v-img position="top" class="white--text" height="200px" :src="info.img">
                            <v-card-title>{{info.lang}}</v-card-title>
                        </v-img> -->
    <!-- <div class="blue lighten-5">
      <v-card-title>{{ info.icon }} {{ info.name }}</v-card-title>
      <v-card-text>Your {{ info.name }} files</v-card-text>
    </div> -->
    <!-- <v-divider></v-divider> -->
    <v-list class="pa-0">
      <v-list-item-group mandatory color="gray">
        <v-list-item v-for="(item, i) in items[info.langCode]" :key="i"
          @change="selectAndLoadPreview(info.langCode, item.name, item.guid)">
          <v-list-item-icon>
            <v-icon>mdi-text-box-outline</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title v-text="item.name"></v-list-item-title>
            {{item.guid}}
          </v-list-item-content>
          <v-icon v-if="item.has_proxy">mdi-translate</v-icon>
        </v-list-item>
      </v-list-item-group>
    </v-list>
    <v-divider></v-divider>
    <v-card-title>Upload</v-card-title>
    <v-card-text>Upload raw {{ info.name }} document in txt format.</v-card-text>
    <v-card-actions>
      <v-file-input outlined dense accept=".txt" @change="onFileChange($event, info.langCode)">
      </v-file-input>
    </v-card-actions>
    <v-divider></v-divider>
    <v-card-actions>
      <v-btn @click="uploadFile(info.langCode)" :loading="isLoading.upload[info.langCode]"
        :disabled="isLoading.upload[info.langCode]">
        Upload
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
  export default {
    name: "RawPanel",
    props: ["info", "isLoading", "items"],
    methods: {
      onFileChange(event, langCode) {
        this.$emit('onFileChange', event, langCode)
      },
      uploadFile(langCode) {
        this.$emit('uploadFile', langCode)
      },
      selectAndLoadPreview(langCode, item, id) {
        this.$emit('selectAndLoadPreview', langCode, item, id)
      }
    },
    computed: {}
  };
</script>
