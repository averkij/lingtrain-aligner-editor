<template>
  <v-card>
    <!-- <v-img position="top" class="white--text" height="200px" :src="info.img">
                            <v-card-title>{{info.lang}}</v-card-title>
                        </v-img> -->
    <div class="blue lighten-5">
      <v-card-title>{{ info.icon }} Документы</v-card-title>
      <v-card-text>Загруженные ранее файлы</v-card-text>
    </div>
    <v-divider></v-divider>
    <v-list class="pa-0">
      <v-list-item-group mandatory color="gray">
        <v-list-item v-for="(item, i) in items[info.langCode]" :key="i"
          @change="selectAndLoadPreview(info.langCode, item, i)">
          <v-list-item-icon>
            <v-icon>mdi-arrow-right</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title v-text="item"></v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list-item-group>
    </v-list>
    <v-divider></v-divider>
    <v-card-title>Загрузить</v-card-title>
    <v-card-text>Выберите текст на русском языке в формате .txt</v-card-text>
    <v-card-actions>
      <v-file-input outlined dense accept=".txt" @change="onFileChange($event, info.langCode)">
      </v-file-input>
    </v-card-actions>
    <v-divider></v-divider>
    <v-card-actions>
      <v-btn @click="uploadFile(info.langCode)" :loading="isLoading.upload[info.langCode]"
        :disabled="isLoading.upload[info.langCode]">
        Загрузить
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
      selectAndLoadPreview(langCode, item, index) {
        this.$emit('selectAndLoadPreview', langCode, item, index)
      }
    },
    computed: {}
  };
</script>